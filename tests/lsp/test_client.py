import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from lsp.client import LspError, get_diagnostics


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
