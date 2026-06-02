from collections import deque
from datetime import datetime
from typing import Any, Deque, Dict, List, Optional


# short term memory config

DEFAULT_MEMORY_LIMIT = 20


# short term memory sys

class ShortTermMemory:
    """
    Session-level conversational memory.

    Responsibilities:
    - maintain active workflow context
    - store recent interactions
    - support immediate reasoning
    - provide conversational continuity
    """

    def __init__(
        self,
        memory_limit: int = DEFAULT_MEMORY_LIMIT
    ):

        self.memory_limit = memory_limit

        self.memory_buffer: Deque = deque(
            maxlen=memory_limit
        )


    # add memory

    def add_memory(
        self,
        role: str,
        content: str,
        metadata: Optional[
            Dict[str, Any]
        ] = None
    ) -> None:
        """
        Store conversational interaction.
        """

        memory_entry = {

            "timestamp": (
                datetime.utcnow()
                .isoformat()
            ),

            "role": role,

            "content": content,

            "metadata": metadata or {}
        }

        self.memory_buffer.append(
            memory_entry
        )


    # get recent memories 

    def get_recent_memories(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recent conversation history.
        """

        return list(
            self.memory_buffer
        )[-limit:]


    # get full context 

    def get_context(self) -> str:
        """
        Build conversational context string.
        """

        context_parts = []

        for memory in self.memory_buffer:

            role = memory["role"]

            content = memory["content"]

            context_parts.append(
                f"{role}: {content}"
            )

        return "\n".join(context_parts)


    # search memory

    def search_memory(
        self,
        keyword: str
    ) -> List[Dict[str, Any]]:
        """
        Keyword-based short-term memory search.
        """

        keyword = keyword.lower()

        matches = []

        for memory in self.memory_buffer:

            content = (
                memory["content"]
                .lower()
            )

            if keyword in content:

                matches.append(memory)

        return matches


    # clear memory

    def clear_memory(self) -> None:
        """
        Reset short-term memory.
        """

        self.memory_buffer.clear()


    # memory size

    def memory_size(self) -> int:
        """
        Current memory entry count.
        """

        return len(self.memory_buffer)


# global helper 

short_term_memory = (
    ShortTermMemory()
)