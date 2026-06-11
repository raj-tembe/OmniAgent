import json
import os
import logging
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional
from config import MEMORY_STORAGE_DIR


# memory manager class

class MemoryManager:
    """
    Centralized memory management system.

    Responsibilities:
    - Store workflow memories
    - Retrieve historical context
    - Persist execution history
    - Manage long-term memory
    - Support autonomous learning
    """

    def __init__(
        self,
        session_id: str = "default_session"
    ):

        self.session_id = session_id
        self._lock = threading.Lock()
        self._max_entries = 500

        self.memory_file = os.path.join(
            str(MEMORY_STORAGE_DIR),
            f"{session_id}.json"
        )

        self.memories = self._load_memories()


    # load memories 

    def _load_memories(self) -> List[Dict[str, Any]]:
        """
        Load memories from storage.
        """

        if not os.path.exists(self.memory_file):
            return []

        try:

            with open(
                self.memory_file,
                "r",
                encoding="utf-8"
            ) as f:

                return json.load(f)

        except Exception as e:
            logging.getLogger(__name__).error("MemoryManager._load_memories failed: %s", e, exc_info=True)

            return []


    # save memories

    def _save_memories(self) -> None:
        """
        Persist memories to disk.
        """

        try:
            with open(
                self.memory_file,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    self.memories,
                    f,
                    indent=2,
                    ensure_ascii=False
                )
        except Exception as e:
            logging.getLogger(__name__).error("MemoryManager._save_memories failed: %s", e, exc_info=True)


    # add memory 

    def add_memory(
        self,
        memory_type: str,
        content: Dict[str, Any]
    ) -> None:
        """
        Add new memory entry with thread safety and size limits.
        """

        memory_entry = {

            "timestamp": (
                datetime.utcnow().isoformat()
            ),

            "memory_type": memory_type,

            "content": content
        }

        with self._lock:
            self.memories.append(memory_entry)
            if len(self.memories) > self._max_entries:
                self.memories = self.memories[-self._max_entries:]
            self._save_memories()


    # get all memories

    def get_all_memories(
        self
    ) -> List[Dict[str, Any]]:
        """
        Return all stored memories.
        """

        return self.memories


    # get memories by type

    def get_memories_by_type(
        self,
        memory_type: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories matching type.
        """

        return [

            memory

            for memory in self.memories

            if memory.get("memory_type")
            == memory_type
        ]


    # search memories

    def search_memories(
        self,
        keyword: str
    ) -> List[Dict[str, Any]]:
        """
        Keyword-based memory search.
        """

        keyword = keyword.lower()

        results = []

        for memory in self.memories:

            memory_str = json.dumps(
                memory
            ).lower()

            if keyword in memory_str:

                results.append(memory)

        return results


    # get recent memories

    def get_recent_memories(
        self,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve most recent memories.
        """

        return self.memories[-limit:]


    # delete memory

    def delete_memory(
        self,
        index: int
    ) -> bool:
        """
        Delete memory by index.
        """

        try:

            del self.memories[index]

            self._save_memories()

            return True

        except Exception:

            return False


    # clear memory

    def clear_memory(self) -> None:
        """
        Remove all stored memories.
        """

        self.memories = []

        self._save_memories()


    # memory statistics

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Return memory statistics.
        """

        memory_types = {}

        for memory in self.memories:

            mem_type = memory.get(
                "memory_type",
                "unknown"
            )

            memory_types[mem_type] = (
                memory_types.get(mem_type, 0)
                + 1
            )

        return {

            "session_id": self.session_id,

            "total_memories": len(
                self.memories
            ),

            "memory_types": memory_types,

            "memory_file": self.memory_file
        }

# global memory helper

def get_memory_manager(
    session_id: str = "default_session"
) -> MemoryManager:
    """
    Returns memory manager instance.
    """

    return MemoryManager(
        session_id=session_id
    )