"""
General-purpose subagent spawn ("task" tool equivalent).

Lets a calling agent spawn a bounded, scoped subagent mid-workflow and get
back a summarized result, without polluting the parent conversation's
context with the subagent's intermediate reasoning. OmniAgent's graph nodes
don't run a free-form tool-calling loop (each node is a single
structured-output chain), so this is exposed as a plain callable other agent
modules can invoke at a specific decision point — not as something the LLM
decides to call mid-generation.

`run_subagent` is intentionally a *fresh* LLM call: no access to the calling
agent's conversation history, only whatever `context` is explicitly passed
in. That isolation is the point — it keeps the subagent's exploratory
back-and-forth out of the parent's context window.
"""
import logging
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate

from agents.llm import llm
from bus import bus, AgentCompleted, AgentStarted

logger = logging.getLogger(__name__)

_SUBAGENT_SYSTEM_PROMPT = """
You are a scoped, single-purpose subagent inside OmniAgent, spawned to
investigate one bounded task and report back a concise result. You have no
memory of any other part of the workflow beyond what's given to you below.

Answer only the task given. Be concise — you are producing a summary another
agent will read, not a full report.
"""


def run_subagent(task: str, context: str = "", session_id: Optional[str] = None) -> str:
    """
    Spawn a bounded, one-shot "general-purpose" subagent to investigate
    `task`, optionally given `context` (e.g. recent error messages, critic
    feedback). Returns the subagent's plain-text summary.

    Publishes AgentStarted/AgentCompleted on the bus with agent="task" so
    this shows up in the same event stream as the main graph nodes.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", _SUBAGENT_SYSTEM_PROMPT),
        ("human", "Task:\n{task}\n\nContext:\n{context}"),
    ])

    bus.publish(AgentStarted(agent="task", session_id=session_id))

    try:
        chain = prompt | llm()
        response = chain.invoke({"task": task, "context": context or "(none provided)"})
        result = getattr(response, "content", str(response)).strip()
    except Exception as exc:
        logger.error("Subagent task failed: %s", exc, exc_info=True)
        result = f"Subagent task failed: {exc}"
    finally:
        bus.publish(AgentCompleted(agent="task", session_id=session_id))

    return result
