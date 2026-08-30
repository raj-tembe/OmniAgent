import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tools.code_tools.edit_tool import EditTool


class TestEditTool(unittest.TestCase):

    def test_replaces_unique_match(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.py"
            path.write_text("def foo():\n    return 1\n")

            with patch("tools.code_tools.edit_tool._resolve_allowed_path", return_value=path):
                result = EditTool.apply_edit(str(path), "return 1", "return 2")

            self.assertTrue(result["success"])
            self.assertEqual(path.read_text(), "def foo():\n    return 2\n")

    def test_fails_when_old_str_not_found(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.py"
            path.write_text("def foo():\n    return 1\n")

            with patch("tools.code_tools.edit_tool._resolve_allowed_path", return_value=path):
                result = EditTool.apply_edit(str(path), "return 999", "return 2")

            self.assertFalse(result["success"])
            self.assertIn("not found", result["error"])
            self.assertEqual(path.read_text(), "def foo():\n    return 1\n")

    def test_fails_when_old_str_not_unique(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.py"
            path.write_text("x = 1\nx = 1\n")

            with patch("tools.code_tools.edit_tool._resolve_allowed_path", return_value=path):
                result = EditTool.apply_edit(str(path), "x = 1", "x = 2")

            self.assertFalse(result["success"])
            self.assertIn("not unique", result["error"])
            # file must be untouched
            self.assertEqual(path.read_text(), "x = 1\nx = 1\n")

    def test_disallowed_path_fails_gracefully(self):
        with patch(
            "tools.code_tools.edit_tool._resolve_allowed_path",
            side_effect=ValueError("outside allowed roots"),
        ):
            result = EditTool.apply_edit("/etc/passwd", "a", "b")

        self.assertFalse(result["success"])
        self.assertIn("outside allowed roots", result["error"])


if __name__ == "__main__":
    unittest.main()
