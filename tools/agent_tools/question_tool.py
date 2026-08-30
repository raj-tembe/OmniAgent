import logging
import sys
from typing import Callable, Optional

from bus import bus, PermissionRequested, PermissionResolved

logger = logging.getLogger(__name__)


def _default_prompt(question: str, context: Optional[str]) -> str:
    print(f"\n[AGENT QUESTION] {question}")
    if context:
        print(f"Context: {context}")
    return input("Your answer: ").strip()


class QuestionTool:
    """
    Lets an agent pause and ask the user a clarifying question mid-task,
    instead of guessing and pressing on. Reuses the permission engine's
    request/resolve event pair on the bus (a question is, structurally, a
    request for a decision the agent can't make on its own) so a future IDE
    panel can render both the same way without a separate event type.
    """

    @staticmethod
    def ask(
        question: str,
        context: Optional[str] = None,
        interactive: bool = False,
        session_id: Optional[str] = None,
        prompt: Callable[[str, Optional[str]], str] = _default_prompt,
    ) -> Optional[str]:
        """
        Ask `question`. Returns the user's answer if running interactively
        with a TTY attached; otherwise returns None (and logs it) so the
        calling agent falls back to its own best judgment rather than
        blocking a non-interactive run forever.
        """
        bus.publish(PermissionRequested(tool="question", agent="", reason=question, session_id=session_id))

        if not (interactive and sys.stdin.isatty()):
            logger.info("Non-interactive run — question was not asked: %s", question)
            bus.publish(PermissionResolved(tool="question", decision="deny", session_id=session_id))
            return None

        answer = prompt(question, context)
        bus.publish(PermissionResolved(tool="question", decision="allow", session_id=session_id))
        return answer
