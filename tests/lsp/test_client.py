import itertools
import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

from lsp.client import LspError, _wait_for_diagnostics, get_diagnostics


class TestGetDiagnosticsErrorPaths(unittest.TestCase):

    def test_unsupported_extension_raises_before_spawning_anything(self):
        with self.assertRaises(LspError) as ctx:
            get_diagnostics("/tmp/whatever.rb")
        self.assertIn("No language server configured", str(ctx.exception))

    def test_missing_file_with_no_content_override_raises_oserror(self):
        # unsupported-extension check happens first; use a .py path that
        # doesn't exist and no `content=` override, so the read itself fails
        with self.assertRaises(OSError):
            get_diagnostics("/nonexistent/path/does_not_exist.py")


class TestWaitForDiagnosticsSettleWindow(unittest.TestCase):
    """
    Real bug found in live verification: rust-analyzer publishes an initial
    (empty) diagnostics result immediately after didOpen, then a real one
    once analysis actually finishes. Returning on the first match reported
    "no issues" for a file with a genuine type error, after ~3 seconds, well
    under any reasonable timeout. These tests prove the settle-window fix
    keeps the LATEST publish for a URI, not the first.
    """

    @staticmethod
    def _fake_connection(*scripted_messages):
        conn = MagicMock()
        # after the scripted messages run out, keep returning None forever —
        # a fixed-length side_effect list would raise StopIteration instead,
        # which doesn't represent "nothing more arrived" the way real
        # next_message() timing out over and over does
        conn.next_message.side_effect = itertools.chain(scripted_messages, itertools.repeat(None))
        return conn

    def test_later_publish_for_same_uri_supersedes_earlier_one(self):
        import time

        conn = self._fake_connection(
            {"method": "textDocument/publishDiagnostics", "params": {"uri": "file:///a.rs", "diagnostics": []}},
            {"method": "textDocument/publishDiagnostics", "params": {"uri": "file:///a.rs", "diagnostics": [
                {"severity": 1, "message": "mismatched types", "range": {"start": {"line": 1, "character": 4}}, "source": "rust-analyzer"},
            ]}},
        )

        result = _wait_for_diagnostics(conn, "file:///a.rs", deadline=time.time() + 10, settle_seconds=0.05)

        self.assertEqual(len(result), 1)
        self.assertIn("mismatched types", result[0]["message"])

    def test_single_publish_is_still_returned_after_settle_window(self):
        import time

        conn = self._fake_connection(
            {"method": "textDocument/publishDiagnostics", "params": {"uri": "file:///a.py", "diagnostics": [
                {"severity": 1, "message": "undefined name", "range": {"start": {"line": 0, "character": 0}}, "source": "pyflakes"},
            ]}},
        )

        result = _wait_for_diagnostics(conn, "file:///a.py", deadline=time.time() + 10, settle_seconds=0.05)

        self.assertEqual(len(result), 1)
        self.assertIn("undefined name", result[0]["message"])

    def test_empty_follow_up_after_a_real_result_is_not_dropped_silently(self):
        """
        Also verify the reverse ordering doesn't silently regress: if a real
        result arrives first and an (unusual) empty one follows within the
        settle window, the LATEST one — even if empty — should win, since
        "latest" is the whole point, not "prefer non-empty."
        """
        import time

        conn = self._fake_connection(
            {"method": "textDocument/publishDiagnostics", "params": {"uri": "file:///a.rs", "diagnostics": [
                {"severity": 1, "message": "stale error", "range": {"start": {"line": 0, "character": 0}}},
            ]}},
            {"method": "textDocument/publishDiagnostics", "params": {"uri": "file:///a.rs", "diagnostics": []}},
        )

        result = _wait_for_diagnostics(conn, "file:///a.rs", deadline=time.time() + 10, settle_seconds=0.05)

        self.assertEqual(result, [])

    def test_diagnostics_for_a_different_uri_are_ignored(self):
        import time

        conn = self._fake_connection(
            {"method": "textDocument/publishDiagnostics", "params": {"uri": "file:///other.py", "diagnostics": [
                {"severity": 1, "message": "unrelated", "range": {"start": {"line": 0, "character": 0}}},
            ]}},
        )

        result = _wait_for_diagnostics(conn, "file:///a.py", deadline=time.time() + 0.2, settle_seconds=0.05)

        self.assertEqual(result, [])

    def test_no_publish_at_all_returns_empty_list(self):
        import time

        conn = self._fake_connection()

        result = _wait_for_diagnostics(conn, "file:///a.py", deadline=time.time() + 0.1, settle_seconds=0.05)

        self.assertEqual(result, [])


@unittest.skipUnless(shutil.which("pylsp"), "pylsp not installed in this environment")
class TestGetDiagnosticsAgainstRealPylsp(unittest.TestCase):
    """
    A genuine end-to-end test against a real, live pylsp process — not a
    mock. Skips gracefully if pylsp isn't on PATH rather than failing the
    whole suite in an environment that hasn't installed it.
    """

    def test_catches_undefined_name(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.py"
            path.write_text("def foo():\n    return undefined_variable_xyz\n")

            diagnostics = get_diagnostics(str(path), timeout=25)

        messages = [d["message"] for d in diagnostics]
        self.assertTrue(
            any("undefined_variable_xyz" in m for m in messages),
            f"expected an undefined-name diagnostic, got: {messages}",
        )
        undefined_diag = next(d for d in diagnostics if "undefined_variable_xyz" in d["message"])
        self.assertEqual(undefined_diag["severity"], "error")
        self.assertEqual(undefined_diag["line"], 2)

    def test_clean_file_reports_no_errors(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "clean.py"
            path.write_text('"""A clean module."""\n\n\ndef add(a: int, b: int) -> int:\n    return a + b\n')

            diagnostics = get_diagnostics(str(path), timeout=25)

        errors = [d for d in diagnostics if d["severity"] == "error"]
        self.assertEqual(errors, [])

    def test_content_override_checks_unsaved_content_not_disk(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "clean.py"
            path.write_text("x = 1\n")  # on-disk content is fine

            # but check different, broken content instead
            diagnostics = get_diagnostics(
                str(path),
                content="def foo():\n    return still_undefined\n",
                timeout=25,
            )

        messages = [d["message"] for d in diagnostics]
        self.assertTrue(any("still_undefined" in m for m in messages))


if __name__ == "__main__":
    unittest.main()
