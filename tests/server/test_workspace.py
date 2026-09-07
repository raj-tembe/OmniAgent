import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from server.workspace import WorkspaceError, list_directory, read_file


class TestListDirectory(unittest.TestCase):

    def test_lists_files_and_directories(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "README.md").write_text("hi")

            entries = list_directory(root)

            names = {e["name"] for e in entries}
            self.assertEqual(names, {"src", "README.md"})

    def test_directories_sort_before_files(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "z_file.py").write_text("x")
            (root / "a_dir").mkdir()

            entries = list_directory(root)

            self.assertEqual(entries[0]["name"], "a_dir")
            self.assertTrue(entries[0]["is_dir"])

    def test_denied_directories_are_hidden(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            (root / "node_modules").mkdir()
            (root / "src").mkdir()

            entries = list_directory(root)

            names = {e["name"] for e in entries}
            self.assertEqual(names, {"src"})

    def test_denied_filenames_are_hidden(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".env").write_text("SECRET=1")
            (root / "app.py").write_text("x")

            entries = list_directory(root)

            names = {e["name"] for e in entries}
            self.assertEqual(names, {"app.py"})

    def test_relative_paths_returned_are_root_relative(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("x")

            entries = list_directory(root, relative="src")

            self.assertEqual(entries[0]["path"], "src/main.py")

    def test_path_traversal_is_rejected(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "workspace"
            root.mkdir()

            with self.assertRaises(WorkspaceError):
                list_directory(root, relative="../../etc")

    def test_missing_path_raises_file_not_found(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(FileNotFoundError):
                list_directory(root, relative="nonexistent")

    def test_listing_a_file_raises_not_a_directory(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("x")

            with self.assertRaises(NotADirectoryError):
                list_directory(root, relative="app.py")


class TestReadFile(unittest.TestCase):

    def test_reads_text_content(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("print('hi')\n")

            content = read_file(root, "app.py")

            self.assertEqual(content, "print('hi')\n")

    def test_nested_file_is_readable(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("x = 1\n")

            content = read_file(root, "src/main.py")

            self.assertEqual(content, "x = 1\n")

    def test_path_traversal_is_rejected(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "workspace"
            root.mkdir()
            secret = Path(tmp) / "secret.txt"
            secret.write_text("nope")

            with self.assertRaises(WorkspaceError):
                read_file(root, "../secret.txt")

    def test_denied_filename_is_rejected(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".env").write_text("SECRET=1")

            with self.assertRaises(WorkspaceError):
                read_file(root, ".env")

    def test_binary_extension_is_rejected(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "image.png").write_bytes(b"\x89PNG\r\n")

            with self.assertRaises(WorkspaceError):
                read_file(root, "image.png")

    def test_missing_file_raises_file_not_found(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(FileNotFoundError):
                read_file(root, "nonexistent.py")

    def test_reading_a_directory_raises_is_a_directory(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()

            with self.assertRaises(IsADirectoryError):
                read_file(root, "src")

    def test_non_utf8_content_raises_workspace_error(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data.txt").write_bytes(b"\xff\xfe\x00\x01")

            with self.assertRaises(WorkspaceError):
                read_file(root, "data.txt")


if __name__ == "__main__":
    unittest.main()
