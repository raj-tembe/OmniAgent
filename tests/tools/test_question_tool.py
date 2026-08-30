import unittest
from unittest.mock import patch

from bus.event_bus import EventBus, WILDCARD
import tools.agent_tools.question_tool as question_tool_module
from tools.agent_tools.question_tool import QuestionTool


class TestQuestionTool(unittest.TestCase):

    def setUp(self):
        self.test_bus = EventBus()
        self.patcher = patch.object(question_tool_module, "bus", self.test_bus)
        self.patcher.start()
        self.received = []
        self.test_bus.subscribe(WILDCARD, lambda e: self.received.append((e.type, getattr(e, "decision", None))))

    def tearDown(self):
        self.patcher.stop()

    def test_non_interactive_returns_none_and_denies(self):
        answer = QuestionTool.ask("Which framework?", interactive=False)

        self.assertIsNone(answer)
        self.assertIn(("permission.resolved", "deny"), self.received)

    def test_interactive_without_tty_returns_none(self):
        with patch("sys.stdin.isatty", return_value=False):
            answer = QuestionTool.ask("Which framework?", interactive=True)

        self.assertIsNone(answer)

    def test_interactive_with_tty_prompts_and_returns_answer(self):
        with patch("sys.stdin.isatty", return_value=True):
            answer = QuestionTool.ask(
                "Which framework?",
                interactive=True,
                prompt=lambda q, c: "Flask",
            )

        self.assertEqual(answer, "Flask")
        self.assertIn(("permission.resolved", "allow"), self.received)

    def test_publishes_request_event_with_question_as_reason(self):
        QuestionTool.ask("Which DB?", interactive=False)

        request_events = [e for e in self.received if e[0] == "permission.requested"]
        self.assertEqual(len(request_events), 1)


if __name__ == "__main__":
    unittest.main()
