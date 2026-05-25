from typing import Dict

from langchain_core.messages import AIMessage

from graph.state import AgentState

from agents.memory.memory_manager import (
    get_memory_manager
)

from agents.memory.retrieval import (
    get_memory_retrieval
)


def memory_agent(state: AgentState) -> Dict:
    """
    Memory Agent

    Responsibilities:
    - Persist workflow memories
    - Store successful execution patterns
    - Store runtime failures
    - Build historical context
    - Retrieve relevant memories
    - Support long-term autonomous reasoning
    """

    # extract state

    session_id = state.get(
        "session_id",
        "default_session"
    )

    user_request = state.get(
        "user_request",
        ""
    )

    current_step = state.get(
        "current_step",
        ""
    )

    workflow_status = state.get(
        "workflow_status",
        ""
    )

    execution_success = state.get(
        "execution_success",
        False
    )

    execution_logs = state.get(
        "execution_logs",
        ""
    )

    error_message = state.get(
        "error_message",
        ""
    )

    generated_files = state.get(
        "generated_files",
        {}
    )

    critic_feedback = state.get(
        "critic_feedback",
        ""
    )

    quality_score = state.get(
        "quality_score",
        0
    )

    retry_count = state.get(
        "retry_count",
        0
    )

    next_agent = state.get(
        "next_agent",
        "end"
    )


    # initialize memory manager and retrieval system

    memory_manager = get_memory_manager(
        session_id=session_id
    )

    retrieval_system = get_memory_retrieval(
        session_id=session_id
    )


    # determine memory type

    if execution_success and quality_score >= 8:

        memory_type = "successful_execution"

    elif error_message:

        memory_type = "execution_failure"

    elif critic_feedback:

        memory_type = "critic_feedback"

    else:

        memory_type = "workflow_context"


    # build memory content

    memory_content = {

        "user_request": user_request,

        "current_step": current_step,

        "workflow_status": workflow_status,

        "execution_success": execution_success,

        "quality_score": quality_score,

        "retry_count": retry_count,

        "error_message": error_message,

        "critic_feedback": critic_feedback,

        "generated_files": list(
            generated_files.keys()
        ),

        "execution_logs": (
            execution_logs[:2000]
            if execution_logs
            else ""
        )
    }


    # store memory

    memory_manager.add_memory(
        memory_type=memory_type,
        content=memory_content
    )


    # retrieve relevant memories for context building

    relevant_memories = (
        retrieval_system.get_relevant_memories(
            query=user_request,
            limit=3
        )
    )


    # retrieve similar past failures if current execution failed

    similar_failures = []

    if error_message:

        similar_failures = (
            retrieval_system.get_error_solutions(
                error_message=error_message,
                limit=3
            )
        )


    # memory statistics

    memory_stats = (
        retrieval_system.get_memory_insights()
    )


    # build memory message

    if execution_success:

        memory_message = (
            "🧠 Memory Agent: "
            "Stored successful execution pattern "
            "for future optimization."
        )

    elif error_message:

        memory_message = (
            "🛠️ Memory Agent: "
            "Stored runtime failure and "
            "retrieved similar debugging history."
        )

    else:

        memory_message = (
            "📚 Memory Agent: "
            "Workflow context stored successfully."
        )


    # return updated state

    return {

        "messages": [
            AIMessage(content=memory_message)
        ],

        # Memory Storage
        "memory_type": memory_type,

        "memory_stats": memory_stats,

        # Retrieved Context
        "memory_context": relevant_memories,

        "similar_failures": similar_failures,

        # Workflow
        "next_agent": next_agent,
    }