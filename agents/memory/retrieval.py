from typing import Any, Dict, List, Optional

from agents.memory.memory_manager import (
    get_memory_manager
)


# memory retrieval and context management system

class MemoryRetrieval:
    """
    Memory retrieval and context management system.

    Responsibilities:
    - Retrieve relevant workflow memories
    - Search historical execution patterns
    - Support autonomous reasoning
    - Provide contextual memory to agents
    """

    def __init__(
        self,
        session_id: str = "default_session"
    ):

        self.memory_manager = (
            get_memory_manager(session_id)
        )


    # get relevant memories

    def get_relevant_memories(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories relevant to query.
        """

        matching_memories = (
            self.memory_manager.search_memories(
                query
            )
        )

        return matching_memories[:limit]


    # get failure memories

    def get_failure_memories(
        self,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve previous failure memories.
        """

        failure_memories = []

        all_memories = (
            self.memory_manager.get_all_memories()
        )

        for memory in all_memories:

            content = memory.get(
                "content",
                {}
            )

            if (
                content.get("execution_success")
                is False
            ):

                failure_memories.append(memory)

        return failure_memories[-limit:]


    # get successful patterns

    def get_successful_patterns(
        self,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve successful execution memories.
        """

        successful_memories = []

        all_memories = (
            self.memory_manager.get_all_memories()
        )

        for memory in all_memories:

            content = memory.get(
                "content",
                {}
            )

            quality_score = content.get(
                "quality_score",
                0
            )

            if (
                content.get("execution_success")
                is True
                and quality_score >= 8
            ):

                successful_memories.append(memory)

        return successful_memories[-limit:]


    # get error solutions

    def get_error_solutions(
        self,
        error_message: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve previous fixes for similar errors.
        """

        matching_solutions = []

        all_memories = (
            self.memory_manager.get_all_memories()
        )

        for memory in all_memories:

            content = memory.get(
                "content",
                {}
            )

            previous_error = str(
                content.get(
                    "error_message",
                    ""
                )
            ).lower()

            if (
                error_message.lower()
                in previous_error
            ):

                matching_solutions.append(memory)

        return matching_solutions[:limit]


    # build context for agent

    def build_context_for_agent(
        self,
        agent_name: str,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build contextual memory package
        for workflow agents.
        """

        context = {

            "agent_name": agent_name,

            "recent_memories": (
                self.memory_manager
                .get_recent_memories(limit=5)
            ),

            "successful_patterns": (
                self.get_successful_patterns()
            ),

            "failure_patterns": (
                self.get_failure_memories()
            )
        }

        # Query-specific memory retrieval
        if query:

            context["relevant_memories"] = (
                self.get_relevant_memories(
                    query=query
                )
            )

        return context


    # get execution history

    def get_execution_history(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve workflow execution history.
        """

        all_memories = (
            self.memory_manager.get_all_memories()
        )

        execution_history = []

        for memory in all_memories:

            content = memory.get(
                "content",
                {}
            )

            execution_history.append({

                "timestamp": memory.get(
                    "timestamp"
                ),

                "workflow_status": content.get(
                    "workflow_status"
                ),

                "execution_success": content.get(
                    "execution_success"
                ),

                "quality_score": content.get(
                    "quality_score"
                ),

                "retry_count": content.get(
                    "retry_count"
                )
            })

        return execution_history[-limit:]


    # get memory insights

    def get_memory_insights(
        self
    ) -> Dict[str, Any]:
        """
        Analyze workflow memory trends.
        """

        all_memories = (
            self.memory_manager.get_all_memories()
        )

        total_memories = len(all_memories)

        successful_runs = 0

        failed_runs = 0

        avg_quality = 0

        quality_scores = []

        for memory in all_memories:

            content = memory.get(
                "content",
                {}
            )

            if content.get(
                "execution_success"
            ) is True:

                successful_runs += 1

            elif content.get(
                "execution_success"
            ) is False:

                failed_runs += 1

            score = content.get(
                "quality_score"
            )

            if score is not None:

                quality_scores.append(score)

        if quality_scores:

            avg_quality = (
                sum(quality_scores)
                / len(quality_scores)
            )

        success_rate = 0

        total_runs = (
            successful_runs + failed_runs
        )

        if total_runs > 0:

            success_rate = (
                successful_runs / total_runs
            ) * 100

        return {

            "total_memories": total_memories,

            "successful_runs": successful_runs,

            "failed_runs": failed_runs,

            "success_rate": round(
                success_rate,
                2
            ),

            "average_quality_score": round(
                avg_quality,
                2
            )
        }


#global retrieval helper

def get_memory_retrieval(
    session_id: str = "default_session"
) -> MemoryRetrieval:
    """
    Returns memory retrieval system.
    """

    return MemoryRetrieval(
        session_id=session_id
    )