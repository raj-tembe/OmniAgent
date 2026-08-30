import unittest
from unittest.mock import MagicMock, patch

from bus.event_bus import EventBus, WILDCARD
import agents.subagent as subagent_module
from agents.subagent import run_subagent


class TestRunSubagent(unittest.TestCase):

    def setUp(self):
        self.test_bus = EventBus()
        self.patcher = patch.object(subagent_module, "bus", self.test_bus)
        self.patcher.start()
        self.received = []
        self.test_bus.subscribe(WILDCARD, lambda e: self.received.append((e.type, getattr(e, "agent", None))))

    def tearDown(self):
        self.patcher.stop()

    def test_returns_stripped_content_from_chain(self):
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = MagicMock(content="  root cause: X  ")

        with patch("agents.subagent.llm", return_value=MagicMock()), \
             patch("agents.subagent.ChatPromptTemplate") as mock_template_cls:
            mock_template_cls.from_messages.return_value.__or__ = MagicMock(return_value=mock_chain)
            result = run_subagent("diagnose failure", context="error info")

        self.assertEqual(result, "root cause: X")

    def test_publishes_agent_started_and_completed(self):
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = MagicMock(content="ok")

        with patch("agents.subagent.llm", return_value=MagicMock()), \
             patch("agents.subagent.ChatPromptTemplate") as mock_template_cls:
            mock_template_cls.from_messages.return_value.__or__ = MagicMock(return_value=mock_chain)
            run_subagent("task", session_id="abc")

        self.assertIn(("agent.started", "task"), self.received)
        self.assertIn(("agent.completed", "task"), self.received)

    def test_exception_in_chain_returns_error_string_and_still_publishes_completed(self):
        with patch("agents.subagent.llm", return_value=MagicMock()), \
             patch("agents.subagent.ChatPromptTemplate") as mock_template_cls:
            broken_chain = MagicMock()
            broken_chain.invoke.side_effect = RuntimeError("llm exploded")
            mock_template_cls.from_messages.return_value.__or__ = MagicMock(return_value=broken_chain)

            result = run_subagent("task")

        self.assertIn("Subagent task failed", result)
        self.assertIn(("agent.completed", "task"), self.received)


if __name__ == "__main__":
    unittest.main()
