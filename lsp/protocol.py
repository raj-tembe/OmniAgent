"""
JSON-RPC over stdio — the transport every LSP server speaks.

Messages are framed as `Content-Length: N\\r\\n\\r\\n<N bytes of JSON>`. This
module only knows about that framing and process lifecycle; it has no idea
what "initialize" or "textDocument/didOpen" mean — that's lsp/client.py's
job. Reading happens on a background thread pushing onto a queue, since a
language server can send unsolicited notifications ($/progress,
window/logMessage) in between the responses we're actually waiting for, and
a single blocking read wouldn't let us skip past those.
"""
import json
import queue
import subprocess
import threading
from typing import Any, Dict, List, Optional


class JsonRpcConnection:
    """A live JSON-RPC connection to a spawned language server process."""

    def __init__(self, process: subprocess.Popen):
        self.process = process
        self._next_id = 1
        self._incoming: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._reader_thread.start()

    @classmethod
    def spawn(cls, command: List[str]) -> "JsonRpcConnection":
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        return cls(process)

    def _read_loop(self) -> None:
        stdout = self.process.stdout
        try:
            while True:
                headers: Dict[str, str] = {}
                while True:
                    line = stdout.readline()
                    if not line:
                        return  # process closed its stdout
                    decoded = line.decode("ascii", errors="replace").strip()
                    if decoded == "":
                        break
                    if ":" in decoded:
                        key, _, value = decoded.partition(":")
                        headers[key.strip().lower()] = value.strip()

                length = int(headers.get("content-length", 0))
                if length <= 0:
                    continue

                body = stdout.read(length)
                if not body:
                    return
                message = json.loads(body.decode("utf-8"))
                self._incoming.put(message)
        except (ValueError, OSError):
            return

    def send(self, message: Dict[str, Any]) -> None:
        body = json.dumps(message).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        self.process.stdin.write(header + body)
        self.process.stdin.flush()

    def send_request(self, method: str, params: Dict[str, Any]) -> int:
        """Send a request and return its id, so the caller can match the response."""
        msg_id = self._next_id
        self._next_id += 1
        self.send({"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params})
        return msg_id

    def send_notification(self, method: str, params: Dict[str, Any]) -> None:
        self.send({"jsonrpc": "2.0", "method": method, "params": params})

    def next_message(self, timeout: float) -> Optional[Dict[str, Any]]:
        """Block for up to `timeout` seconds for the next incoming message."""
        try:
            return self._incoming.get(timeout=timeout)
        except queue.Empty:
            return None

    def close(self) -> None:
        for stream in (self.process.stdin, self.process.stdout):
            try:
                stream.close()
            except Exception:
                pass
        try:
            self.process.terminate()
        except Exception:
            pass
