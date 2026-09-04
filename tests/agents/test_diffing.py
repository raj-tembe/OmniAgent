import unittest

from agents.diffing import compute_file_diffs


class TestComputeFileDiffs(unittest.TestCase):

    def test_new_file_is_marked_added(self):
        result = compute_file_diffs({}, {"app.py": "print(1)\n"})

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["filename"], "app.py")
        self.assertEqual(result[0]["change_type"], "added")
        self.assertIn("+print(1)", result[0]["diff"])

    def test_modified_file_shows_both_removed_and_added_lines(self):
        before = {"app.py": "x = 1\n"}
        after = {"app.py": "x = 2\n"}

        result = compute_file_diffs(before, after)

        self.assertEqual(result[0]["change_type"], "modified")
        self.assertIn("-x = 1", result[0]["diff"])
        self.assertIn("+x = 2", result[0]["diff"])

    def test_unchanged_file_produces_no_diff(self):
        content = {"app.py": "same content\n"}

        result = compute_file_diffs(content, content)

        self.assertEqual(result, [])

    def test_multiple_files_only_changed_ones_appear(self):
        before = {"a.py": "1\n", "b.py": "unchanged\n"}
        after = {"a.py": "2\n", "b.py": "unchanged\n", "c.py": "new\n"}

        result = compute_file_diffs(before, after)

        filenames = {r["filename"] for r in result}
        self.assertEqual(filenames, {"a.py", "c.py"})

    def test_diff_includes_file_headers(self):
        result = compute_file_diffs({}, {"app.py": "x\n"})

        self.assertIn("a/app.py", result[0]["diff"])
        self.assertIn("b/app.py", result[0]["diff"])

    def test_empty_before_and_after_produces_nothing(self):
        self.assertEqual(compute_file_diffs({}, {}), [])


if __name__ == "__main__":
    unittest.main()
