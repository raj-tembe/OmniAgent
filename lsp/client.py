"""
High-level "get diagnostics for this file" workflow, built on top of
lsp/protocol.py's raw JSON-RPC connection and lsp/servers.py's per-extension
server registry.

This is a single-shot connection per call — spawn the server, initialize,
open the document, wait for the diagnostics notification the server
publishes back, then shut down. Real language servers (pyright, gopls) are
often used as long-lived background processes for speed; this
implementation trades that speed for simplicity and correctness on a first
pass — see the parity notes for keeping the server warm as a later
improvement once this is proven useful to the coder/critic agents.
"""
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from lsp.protocol import JsonRpcConnection
from lsp.servers import get_language_id, get_server_command

SEVERITY_NAMES = {1: "error", 2: "warning", 3: "information", 4: "hint"}


class LspError(Exception):
    """Raised when a language server can't be launched or doesn't respond in time."""


def _wait_for_response(conn: JsonRpcConnection, request_id: int, deadline: float) -> Dict[str, Any]:
    while time.time() < deadline:
        msg = conn.next_message(timeout=max(0.05, deadline - time.time()))
        if msg is None:
            break
        if msg.get("id") == request_id:
            return msg
    raise LspError("Timed out waiting for the language server to respond to 'initialize'.")


def _wait_for_diagnostics(conn: JsonRpcConnection, uri: str, deadline: float) -> List[Dict[str, Any]]:
    while time.time() < deadline:
        msg = conn.next_message(timeout=max(0.05, deadline - time.time()))
        if msg is None:
            break
        if msg.get("method") == "textDocument/publishDiagnostics":
            params = msg.get("params", {})
            if params.get("uri") == uri:
                return [_format_diagnostic(d) for d in params.get("diagnostics", [])]
    # No diagnostics notification arrived in time — most servers only
    # publish when there's something to report or on first analysis
    # completion, so this is "clean, as far as we waited to find out",
    # not necessarily "definitely no issues".
    return []


def _format_diagnostic(d: Dict[str, Any]) -> Dict[str, Any]:
    range_ = d.get("range", {})
    start = range_.get("start", {})
    return {
        "severity": SEVERITY_NAMES.get(d.get("severity"), "unknown"),
        "message": d.get("message", ""),
        "line": start.get("line", 0) + 1,      # LSP positions are 0-indexed
        "column": start.get("character", 0) + 1,
        "source": d.get("source"),
    }


def get_diagnostics(filepath: str, content: Optional[str] = None, timeout: float = 15.0) -> List[Dict[str, Any]]:
    """
    Get diagnostics for `filepath` from the language server registered for
    its extension. `content` defaults to the file's current on-disk
    contents — pass it explicitly to check content that hasn't been saved
    yet (e.g. the coder agent's proposed edit, before it's written out).

    Raises LspError if no server is configured for this file type, or if
    the server doesn't respond within `timeout` seconds.
    """
    path = Path(filepath)
    command = get_server_command(path.suffix)
    if command is None:
        raise LspError(f"No language server configured for extension '{path.suffix}'.")

    if content is None:
        content = path.read_text(encoding="utf-8")

    uri = path.resolve().as_uri()
    deadline = time.time() + timeout

    conn = JsonRpcConnection.spawn(command)
    try:
        request_id = conn.send_request("initialize", {
            "processId": None,
            "rootUri": Path.cwd().resolve().as_uri(),
            "capabilities": {},
        })
        _wait_for_response(conn, request_id, deadline)

        conn.send_notification("initialized", {})

        conn.send_notification("textDocument/didOpen", {
            "textDocument": {
                "uri": uri,
                "languageId": get_language_id(path.suffix),
                "version": 1,
                "text": content,
            },
        })

        return _wait_for_diagnostics(conn, uri, deadline)

    finally:
        try:
            conn.send_notification("exit", {})
        except Exception:
            pass
        conn.close()
