import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from memory.vector_store.chroma_store import (
    vector_store
)


# long term memory sys

class LongTermMemory:
    """
    Persistent semantic memory system.

    Responsibilities:
    - store important workflow experiences
    - maintain semantic memory retrieval
    - support contextual reasoning
    - enable historical intelligence
    """

    def __init__(self):

        self.vector_store = vector_store


    # store memory

    def store_memory(
        self,
        content: str,
        memory_type: str,
        metadata: Optional[
            Dict[str, Any]
        ] = None
    ) -> Dict:
        """
        Persist semantic memory.
        """

        try:

            memory_id = str(uuid.uuid4())

            enriched_metadata = {

                "memory_type": memory_type,

                "created_at": (
                    datetime.utcnow()
                    .isoformat()
                ),

                **(metadata or {})
            }

            result = (
                self.vector_store.add_memory(

                    memory_id=memory_id,

                    text=content,

                    metadata=enriched_metadata
                )
            )

            return {

                "success": result["success"],

                "memory_id": memory_id
            }

        except Exception as e:

            return {

                "success": False,

                "error": str(e)
            }


    # retrieve memories

    def retrieve_memories(
        self,
        query: str,
        limit: int = 5
    ) -> Dict:
        """
        Perform semantic memory retrieval.
        """

        return (
            self.vector_store.search_memories(

                query=query,

                limit=limit
            )
        )


    # store workflow experience 

    def store_workflow_experience(
        self,
        user_request: str,
        outcome: str,
        quality_score: float,
        metadata: Optional[
            Dict[str, Any]
        ] = None
    ) -> Dict:
        """
        Store autonomous workflow experience.
        """

        memory_content = f"""
User Request:
{user_request}

Workflow Outcome:
{outcome}

Quality Score:
{quality_score}
"""

        return self.store_memory(

            content=memory_content,

            memory_type="workflow_experience",

            metadata=metadata
        )


    # store error memory 

    def store_error_memory(
        self,
        error_message: str,
        fix_strategy: str,
        metadata: Optional[
            Dict[str, Any]
        ] = None
    ) -> Dict:
        """
        Store debugging/failure memory.
        """

        memory_content = f"""
Execution Error:
{error_message}

Fix Strategy:
{fix_strategy}
"""

        return self.store_memory(

            content=memory_content,

            memory_type="error_recovery",

            metadata=metadata
        )


    # retrieve similar failure 

    def retrieve_similar_failures(
        self,
        error_message: str,
        limit: int = 3
    ) -> Dict:
        """
        Retrieve semantically similar failures.
        """

        return self.retrieve_memories(

            query=error_message,

            limit=limit
        )


    # memory stats

    def get_memory_stats(self) -> Dict:
        """
        Retrieve vector memory statistics.
        """

        try:

            memory_count = (
                self.vector_store
                .count_memories()
            )

            return {

                "success": True,

                "total_memories": memory_count
            }

        except Exception as e:

            return {

                "success": False,

                "error": str(e)
            }


# global helper 

long_term_memory = (
    LongTermMemory()
)