import tempfile
import unittest
from pathlib import Path

from agents.executor.sandbox_runner import _safe_child_path


class TestSandboxRunner(unittest.TestCase):

    def test_safe_child_path_rejects_parent_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                _safe_child_path(Path(directory), "../escape.py")

    def test_safe_child_path_allows_nested_relative_path(self):
        with tempfile.TemporaryDirectory() as directory:
            result = _safe_child_path(Path(directory), "templates/index.html")

        self.assertTrue(str(result).endswith("templates/index.html"))


if __name__ == "__main__":
    unittest.main()
