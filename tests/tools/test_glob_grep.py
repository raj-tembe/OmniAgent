import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tools.code_tools.glob_tool import GlobTool
from tools.code_tools.grep_tool import GrepTool


class TestGlobTool(unittest.TestCase):

    def test_finds_matching_files(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "a.py").write_text("x = 1")
            (root / "src" / "b.py").write_text("y = 2")
            (root / "src" / "c.txt").write_text("not python")

            with patch("tools.code_tools.glob_tool.PROJECT_ROOT", str(root)), \
                 patch("tools.code_tools.glob_tool._resolve_allowed_path", return_value=root):
                result = GlobTool.find("**/*.py", directory=str(root))

            self.assertTrue(result["success"])
            self.assertEqual(len(result["matches"]), 2)
            self.assertTrue(all(m.endswith(".py") for m in result["matches"]))

    def test_skips_hidden_directories(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            (root / ".git" / "config.py").write_text("hidden")
            (root / "visible.py").write_text("shown")

            with patch("tools.code_tools.glob_tool._resolve_allowed_path", return_value=root):
                result = GlobTool.find("**/*.py", directory=str(root))

            self.assertEqual(len(result["matches"]), 1)
            self.assertIn("visible.py", result["matches"][0])

    def test_respects_max_results(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(5):
                (root / f"f{i}.py").write_text("x")

            with patch("tools.code_tools.glob_tool._resolve_allowed_path", return_value=root):
                result = GlobTool.find("*.py", directory=str(root), max_results=2)

            self.assertEqual(len(result["matches"]), 2)
            self.assertTrue(result["truncated"])

    def test_disallowed_path_fails_gracefully(self):
        with patch(
            "tools.code_tools.glob_tool._resolve_allowed_path",
            side_effect=ValueError("outside allowed roots"),
        ):
            result = GlobTool.find("*.py", directory="/etc")

        self.assertFalse(result["success"])
        self.assertIn("outside allowed roots", result["error"])


class TestGrepTool(unittest.TestCase):

    def test_finds_matching_lines(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.py").write_text("def foo():\n    return TODO_MARKER\n")
            (root / "b.py").write_text("def bar():\n    return 1\n")

            with patch("tools.code_tools.grep_tool._resolve_allowed_path", return_value=root):
                result = GrepTool.search("TODO_MARKER", directory=str(root))

            self.assertTrue(result["success"])
            self.assertEqual(len(result["matches"]), 1)
            self.assertEqual(result["matches"][0]["line_number"], 2)
            self.assertIn("a.py", result["matches"][0]["file"])

    def test_literal_search_when_regex_false(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.py").write_text("price = a.b.c\n")

            with patch("tools.code_tools.grep_tool._resolve_allowed_path", return_value=root):
                result = GrepTool.search("a.b.c", directory=str(root), regex=False)

            self.assertEqual(len(result["matches"]), 1)

    def test_invalid_regex_returns_error(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("tools.code_tools.grep_tool._resolve_allowed_path", return_value=root):
                result = GrepTool.search("(unclosed", directory=str(root))

            self.assertFalse(result["success"])
            self.assertIn("Invalid regex", result["error"])

    def test_skips_binary_like_extensions(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            (root / "a.py").write_text("match_me\n")

            with patch("tools.code_tools.grep_tool._resolve_allowed_path", return_value=root):
                result = GrepTool.search("match_me", directory=str(root))

            self.assertEqual(len(result["matches"]), 1)
            self.assertIn("a.py", result["matches"][0]["file"])


if __name__ == "__main__":
    unittest.main()
