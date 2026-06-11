"""
Human approval node.
Pauses the workflow and waits for human input via stdin (CLI) or sets
approved=False automatically in non-interactive environments.
"""
import sys
from typing import Dict
from langchain_core.messages import AIMessage
from graph.state import AgentState


def human_node(state: AgentState) -> Dict:
    """
    Human-in-the-loop approval node.
    In a TTY environment, prompts the user. Otherwise auto-denies.
    """
    reason = state.get("critic_feedback", "Agent requested human review.")
    print(f"\n[HUMAN APPROVAL REQUIRED]\n{reason}\n")

    approved = False
    feedback = ""

    if sys.stdin.isatty():
        answer = input("Approve? (y/n): ").strip().lower()
        approved = answer == "y"
        if not approved:
            feedback = input("Feedback (optional): ").strip()
    else:
        print("Non-interactive environment — auto-denying.")

    return {
        "messages": [AIMessage(content=f"Human node: {'Approved' if approved else 'Denied'}.")],
        "approved": approved,
        "human_feedback": feedback,
        "next_agent": "coder" if approved else "end",
        "current_agent": "human",
    }
