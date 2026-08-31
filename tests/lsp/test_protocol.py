import json
import queue
import unittest
from unittest.mock import MagicMock

from lsp.protocol import JsonRpcConnection


def _framed(message: dict) -> bytes:
    body = json.dumps(message).encode("utf-8")
    return f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body


class FakeStdout:
    """
    A minimal stand-in for a subprocess's stdout pipe: readline() serves
    lines from a pre-framed byte buffer, read(n) serves raw bytes. Lets us
    test the framing/reader-thread logic without a real subprocess.
    """

    def __init__(self, data: bytes):
        self._data = data
        self._pos = 0

    def readline(self) -> bytes:
        if self._pos >= len(self._data):
            return b""
        end = self._data.find(b"\n", self._pos)
        if end == -1:
            chunk = self._data[self._pos:]
            self._pos = len(self._data)
            return chunk
        chunk = self._data[self._pos:end + 1]
        self._pos = end + 1
        return chunk

    def read(self, n: int) -> bytes:
        chunk = self._data[self._pos:self._pos + n]
        self._pos += len(chunk)
        return chunk


def _connection_with_fake_stdout(data: bytes) -> JsonRpcConnection:
    process = MagicMock()
    process.stdout = FakeStdout(data)
    process.stdin = MagicMock()
    return JsonRpcConnection(process)


class TestJsonRpcConnectionReading(unittest.TestCase):

    def test_reads_single_framed_message(self):
        data = _framed({"jsonrpc": "2.0", "id": 1, "result": {"ok": True}})
        conn = _connection_with_fake_stdout(data)

        msg = conn.next_message(timeout=2)

        self.assertEqual(msg["id"], 1)
        self.assertEqual(msg["result"], {"ok": True})

    def test_reads_multiple_framed_messages_in_order(self):
        data = _framed({"jsonrpc": "2.0", "method": "first"}) + _framed({"jsonrpc": "2.0", "method": "second"})
        conn = _connection_with_fake_stdout(data)

        first = conn.next_message(timeout=2)
        second = conn.next_message(timeout=2)

        self.assertEqual(first["method"], "first")
        self.assertEqual(second["method"], "second")

    def test_no_message_available_times_out_to_none(self):
        conn = _connection_with_fake_stdout(b"")
        self.assertIsNone(conn.next_message(timeout=0.2))


class TestJsonRpcConnectionSending(unittest.TestCase):

    def test_send_request_writes_framed_body_and_returns_id(self):
        conn = _connection_with_fake_stdout(b"")

        request_id = conn.send_request("initialize", {"processId": None})

        self.assertEqual(request_id, 1)
        written = conn.process.stdin.write.call_args[0][0]
        self.assertIn(b"Content-Length:", written)
        self.assertIn(b'"method":"initialize"', written.replace(b" ", b""))

    def test_send_notification_has_no_id(self):
        conn = _connection_with_fake_stdout(b"")

        conn.send_notification("initialized", {})

        written = conn.process.stdin.write.call_args[0][0]
        header, _, body = written.partition(b"\r\n\r\n")
        payload = json.loads(body)
        self.assertNotIn("id", payload)

    def test_request_ids_increment(self):
        conn = _connection_with_fake_stdout(b"")

        first_id = conn.send_request("a", {})
        second_id = conn.send_request("b", {})

        self.assertEqual(second_id, first_id + 1)


if __name__ == "__main__":
    unittest.main()
