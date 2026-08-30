import unittest

from tools.agent_tools.todo_tool import TodoTool


class TestTodoTool(unittest.TestCase):

    def test_write_creates_pending_items(self):
        todos = TodoTool.write(["Write tests", "Fix bug"])

        self.assertEqual(len(todos), 2)
        self.assertTrue(all(t["status"] == "pending" for t in todos))
        self.assertEqual(todos[0]["content"], "Write tests")
        # ids are unique
        self.assertNotEqual(todos[0]["id"], todos[1]["id"])

    def test_update_status_changes_only_matching_item(self):
        todos = TodoTool.write(["a", "b"])
        target_id = todos[0]["id"]

        updated = TodoTool.update_status(todos, target_id, "in_progress")

        self.assertEqual(updated[0]["status"], "in_progress")
        self.assertEqual(updated[1]["status"], "pending")

    def test_update_status_unknown_id_is_a_no_op(self):
        todos = TodoTool.write(["a"])

        updated = TodoTool.update_status(todos, "does-not-exist", "completed")

        self.assertEqual(updated, todos)

    def test_read_summarizes_counts(self):
        todos = TodoTool.write(["a", "b", "c"])
        todos = TodoTool.update_status(todos, todos[0]["id"], "completed")
        todos = TodoTool.update_status(todos, todos[1]["id"], "in_progress")

        summary = TodoTool.read(todos)

        self.assertEqual(summary["counts"], {"pending": 1, "in_progress": 1, "completed": 1})
        self.assertEqual(summary["todos"], todos)


if __name__ == "__main__":
    unittest.main()
