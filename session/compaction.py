"""
Session context compaction.

`memory/conversation_memory/short_term.py`'s ShortTermMemory already caps
itself with a fixed-size deque — once full, the oldest entries are silently
dropped. That's fine for a rolling "recent context" buffer, but it's not
what should happen to `graph/state.py`'s `messages` list, which is the
actual conversation the checkpointer persists and the graph nodes read from:
silently losing the beginning of a long-running session loses whatever
decisions were made there.

This module is the compaction policy for that list: decide when it's grown
large enough to need trimming, then replace the oldest messages with one
summary message instead of just dropping them. The summary is produced via
`agents.subagent.run_subagent` — an isolated LLM call, same mechanism the
planner's repeated-failure escalation already uses, reused here for its
other natural purpose: reading a chunk of conversation and producing a
short summary of it.
"""
from typing import List

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

#rough token estimate: ~4 characters per token. Good enough for a
#"should we compact" threshold check; not meant to be exact.
_CHARS_PER_TOKEN = 4

DEFAULT_MAX_CONTEXT_TOKENS = 12_000
DEFAULT_KEEP_RECENT = 6


def estimate_tokens(messages: List[BaseMessage]) -> int:
    """Rough token estimate for a list of messages."""
    total_chars = sum(len(str(getattr(m, "content", ""))) for m in messages)
    return total_chars // _CHARS_PER_TOKEN


def should_compact(messages: List[BaseMessage], max_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS) -> bool:
    """Whether `messages` has grown past the point it should be compacted."""
    return estimate_tokens(messages) > max_tokens


def _format_for_summary(messages: List[BaseMessage]) -> str:
    lines = []
    for m in messages:
        role = getattr(m, "type", m.__class__.__name__)
        lines.append(f"{role}: {getattr(m, 'content', '')}")
    return "\n".join(lines)


def compact_messages(
    messages: List[BaseMessage],
    keep_recent: int = DEFAULT_KEEP_RECENT,
    session_id: str = None,
    summarizer=None,
) -> List[BaseMessage]:
    """
    Replace everything except the most recent `keep_recent` messages with one
    summary message. If there's nothing old enough to summarize (the whole
    list already fits in `keep_recent`), returns `messages` unchanged.

    `summarizer` defaults to `agents.subagent.run_subagent` — overridable so
    tests (and any future non-LLM summarization strategy) don't need a real
    model call.
    """
    if len(messages) <= keep_recent:
        return messages

    if summarizer is None:
        from agents.subagent import run_subagent
        summarizer = run_subagent

    to_summarize = messages[:-keep_recent]
    recent = messages[-keep_recent:]

    summary_text = summarizer(
        task=(
            "Summarize the following conversation history into a short paragraph "
            "that preserves any decisions made, files created or modified, and "
            "unresolved issues. This summary will replace the original messages "
            "as the model's only memory of them."
        ),
        context=_format_for_summary(to_summarize),
        session_id=session_id,
    )

    summary_message = SystemMessage(content=f"[Earlier conversation summary]\n{summary_text}")
    return [summary_message] + recent
