import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agents.executor.sandbox_runner import _safe_child_path, save_generated_files


class TestSandboxRunner(unittest.TestCase):

    def test_safe_child_path_rejects_parent_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                _safe_child_path(Path(directory), "../escape.py")

    def test_safe_child_path_allows_nested_relative_path(self):
        with tempfile.TemporaryDirectory() as directory:
            result = _safe_child_path(Path(directory), "templates/index.html")

        self.assertTrue(str(result).endswith("templates/index.html"))


class TestSaveGeneratedFilesWorkspaceOverride(unittest.TestCase):
    """
    Real filesystem checks (no mocking save_generated_files itself) — proves
    the workspace override actually redirects where files land, not just
    that the parameter exists.
    """

    def test_workspace_override_saves_outside_generated_project_dir(self):
        with tempfile.TemporaryDirectory() as workspace_dir, \
             tempfile.TemporaryDirectory() as fallback_dir:
            with patch("agents.executor.sandbox_runner.GENERATED_PROJECT_DIR", fallback_dir):
                project_path = save_generated_files(
                    {"app.py": "print(1)\n"},
                    project_name="myproj",
                    workspace=workspace_dir,
                )

            self.assertTrue(project_path.startswith(workspace_dir))
            self.assertFalse(project_path.startswith(fallback_dir))
            self.assertEqual(
                (Path(project_path) / "app.py").read_text(),
                "print(1)\n",
            )

    def test_no_workspace_falls_back_to_generated_project_dir(self):
        with tempfile.TemporaryDirectory() as fallback_dir:
            with patch("agents.executor.sandbox_runner.GENERATED_PROJECT_DIR", fallback_dir):
                project_path = save_generated_files(
                    {"app.py": "print(1)\n"},
                    project_name="myproj",
                    workspace=None,
                )

            self.assertTrue(project_path.startswith(fallback_dir))

    def test_workspace_still_enforces_path_traversal_protection(self):
        with tempfile.TemporaryDirectory() as workspace_dir:
            with self.assertRaises(ValueError):
                save_generated_files(
                    {"../../escape.py": "malicious\n"},
                    project_name="myproj",
                    workspace=workspace_dir,
                )


if __name__ == "__main__":
    unittest.main()
