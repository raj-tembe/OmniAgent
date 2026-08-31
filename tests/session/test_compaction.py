import unittest
import unittest.mock
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from session.compaction import (
    DEFAULT_KEEP_RECENT,
    compact_messages,
    estimate_tokens,
    should_compact,
)


class TestEstimateTokens(unittest.TestCase):

    def test_empty_list_is_zero(self):
        self.assertEqual(estimate_tokens([]), 0)

    def test_scales_with_content_length(self):
        short = [HumanMessage(content="hi")]
        long = [HumanMessage(content="x" * 4000)]
        self.assertLess(estimate_tokens(short), estimate_tokens(long))


class TestShouldCompact(unittest.TestCase):

    def test_short_history_does_not_need_compaction(self):
        messages = [HumanMessage(content="hi"), AIMessage(content="hello")]
        self.assertFalse(should_compact(messages, max_tokens=1000))

    def test_long_history_needs_compaction(self):
        messages = [HumanMessage(content="x" * 100) for _ in range(200)]
        self.assertTrue(should_compact(messages, max_tokens=1000))


class TestCompactMessages(unittest.TestCase):

    def test_short_list_is_returned_unchanged(self):
        messages = [HumanMessage(content="a"), AIMessage(content="b")]
        result = compact_messages(messages, keep_recent=6)
        self.assertEqual(result, messages)

    def test_long_list_is_compacted_to_summary_plus_recent(self):
        messages = [HumanMessage(content=f"msg {i}") for i in range(10)]
        fake_summarizer = MagicMock(return_value="Summary of early messages.")

        result = compact_messages(messages, keep_recent=3, summarizer=fake_summarizer)

        self.assertEqual(len(result), 4)  # 1 summary + 3 recent
        self.assertIsInstance(result[0], SystemMessage)
        self.assertIn("Summary of early messages.", result[0].content)
        self.assertEqual(result[1:], messages[-3:])

    def test_summarizer_receives_only_the_older_messages(self):
        messages = [HumanMessage(content=f"msg {i}") for i in range(10)]
        fake_summarizer = MagicMock(return_value="summary")

        compact_messages(messages, keep_recent=3, summarizer=fake_summarizer)

        call_kwargs = fake_summarizer.call_args.kwargs
        self.assertIn("msg 0", call_kwargs["context"])
        self.assertIn("msg 6", call_kwargs["context"])
        self.assertNotIn("msg 7", call_kwargs["context"])  # part of "recent", not summarized

    def test_default_summarizer_is_run_subagent_when_not_provided(self):
        messages = [HumanMessage(content=f"msg {i}") for i in range(10)]

        with unittest.mock.patch("agents.subagent.run_subagent", return_value="ok") as mock_run:
            result = compact_messages(messages, keep_recent=3)

        mock_run.assert_called_once()
        self.assertIn("ok", result[0].content)


if __name__ == "__main__":
    unittest.main()
