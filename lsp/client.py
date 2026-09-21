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

#markers checked (in this order at each directory level) to find the
#project a file belongs to. Language-specific ones first so e.g. a Rust
#crate inside a larger .git-tracked monorepo resolves to the crate, not
#the whole repo.
_WORKSPACE_MARKERS = ("Cargo.toml", "pyproject.toml", "setup.py", "package.json", "go.mod", ".git")


def _find_workspace_root(file_path: Path) -> Path:
    """
    Walk up from `file_path`'s directory looking for a project marker, so
    the language server gets pointed at the actual project the file
    belongs to. Falls back to the file's own parent directory if nothing
    is found.

    This fixes a real, confirmed bug: `get_diagnostics` previously always
    used the *calling process's* current working directory as `rootUri`,
    completely unrelated to the file being checked. For a server like
    `pylsp` checking a file inside the same repo the server happens to run
    from, this accidentally worked. For `rust-analyzer` checking a file in
    an unrelated project, it meant the server couldn't discover any
    workspace at all and silently never analyzed the file — confirmed live:
    diagnostics came back correct once pointed at the right root, empty
    every time before.
    """
    current = file_path.resolve().parent
    while True:
        for marker in _WORKSPACE_MARKERS:
            if (current / marker).exists():
                return current
        if current.parent == current:
            break
        current = current.parent
    return file_path.resolve().parent


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


def _wait_for_diagnostics(
    conn: JsonRpcConnection,
    uri: str,
    deadline: float,
    settle_seconds: float = 1.5,
) -> List[Dict[str, Any]]:
    """
    Collect `publishDiagnostics` notifications for `uri`, keeping the most
    recent one rather than returning on the first match.

    Some servers publish diagnostics progressively: rust-analyzer in
    particular can send an initial (sometimes empty) result immediately
    after `didOpen`, then one or more follow-ups as background
    indexing/analysis actually completes. Returning on the first match risks
    reporting "no issues" before the server has finished checking anything
    at all — confirmed live: a file with a genuine type error came back as
    `[]` after ~3 seconds, well under any reasonable timeout, because that
    first (empty) publish won the race.

    After each publish for `uri`, we wait `settle_seconds` for a possible
    follow-up before giving up and returning what we have. Servers that only
    ever publish once (`pylsp`, in practice) only pay this settle delay one
    time, not the full timeout — this isn't "always wait as long as
    possible," it's "give a fast follow-up a chance to arrive."
    """
    latest: Optional[List[Dict[str, Any]]] = None
    settle_deadline: Optional[float] = None

    while True:
        now = time.time()
        current_deadline = deadline if settle_deadline is None else min(deadline, settle_deadline)
        if now >= current_deadline:
            break

        msg = conn.next_message(timeout=max(0.05, current_deadline - now))
        if msg is None:
            continue  # next loop iteration re-checks current_deadline and exits if it's passed

        if msg.get("method") == "textDocument/publishDiagnostics":
            params = msg.get("params", {})
            if params.get("uri") == uri:
                latest = [_format_diagnostic(d) for d in params.get("diagnostics", [])]
                settle_deadline = time.time() + settle_seconds

    # No diagnostics notification arrived in time at all — most servers only
    # publish when there's something to report or on first analysis
    # completion, so this is "clean, as far as we waited to find out", not
    # necessarily "definitely no issues".
    return latest if latest is not None else []


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


def get_diagnostics(
    filepath: str,
    content: Optional[str] = None,
    timeout: float = 15.0,
    settle_seconds: float = 1.5,
) -> List[Dict[str, Any]]:
    """
    Get diagnostics for `filepath` from the language server registered for
    its extension. `content` defaults to the file's current on-disk
    contents — pass it explicitly to check content that hasn't been saved
    yet (e.g. the coder agent's proposed edit, before it's written out).

    `settle_seconds` controls how long to wait after each diagnostics
    publish for a possible follow-up before returning — see
    `_wait_for_diagnostics`'s docstring. The default is tuned for `pylsp`;
    a slower-to-settle server may need a larger value.

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
    workspace_root = _find_workspace_root(path)
    deadline = time.time() + timeout

    conn = JsonRpcConnection.spawn(command)
    try:
        request_id = conn.send_request("initialize", {
            "processId": None,
            "rootUri": workspace_root.as_uri(),
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

        return _wait_for_diagnostics(conn, uri, deadline, settle_seconds=settle_seconds)

    finally:
        try:
            conn.send_notification("exit", {})
        except Exception:
            pass
        conn.close()
