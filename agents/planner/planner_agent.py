"""Core planner logic."""

import logging
from typing import Dict

from langchain_core.messages import AIMessage

from agents.planner.planner_chain import create_planner_chain
from agents.subagent import run_subagent
from graph.state import AgentState
from session import compact_messages, should_compact
from skill import format_skill_list

logger = logging.getLogger(__name__)


def planner_agent(state: AgentState) -> Dict:
    """Plan the next workflow step and route to the appropriate agent."""

    messages = state.get("messages", [])
    if should_compact(messages):
        pre_compact_count = len(messages)
        messages = compact_messages(messages, session_id=state.get("session_id"))
        logger.info(
            "Compacted session history: %d messages -> %d (summary + recent).",
            pre_compact_count, len(messages),
        )

    user_request = state.get(
        "user_request",
        messages[-1].content if messages else "No request provided.",
    )

    plan = state.get("plan", [])
    completed_steps = state.get("completed_steps", [])
    retry_count = state.get("retry_count", 0)
    execution_success = state.get("execution_success", False)
    critic_feedback = state.get("critic_feedback", "")
    error_message = state.get("error_message", "")

    planner_chain = create_planner_chain()

    response = planner_chain.invoke({
        "user_request": user_request,
        "existing_plan": plan,
        "completed_steps": completed_steps,
        "retry_count": retry_count,
        "execution_success": execution_success,
        "critic_feedback": critic_feedback,
        "error_message": error_message,
        "available_skills": format_skill_list(),
    })

    plan = response.tasks
    current_step = response.current_step
    workflow_status = response.workflow_status
    next_agent = response.next_agent

    if getattr(response, "reasoning", None):
        logger.info("Planner reasoning: %s", response.reasoning)

    if getattr(response, "recovery_strategy", None):
        logger.info("Planner recovery strategy: %s", response.recovery_strategy)

    should_request_human = state.get("interactive", False) and bool(
        getattr(response, "require_human_approval", False)
    )

    if workflow_status == "completed":
        next_agent = "end"
        planner_message = (
            "Planner Agent: Workflow planning and execution completed successfully."
        )
    elif should_request_human:
        next_agent = "human"
        planner_message = (
            "Planner Agent: Human approval requested before continuing the workflow."
        )
    elif workflow_status == "researching" or next_agent == "researcher":
        next_agent = "researcher"
        planner_message = (
            "Planner Agent: Research phase required before implementation."
        )
    elif retry_count >= 3:
        next_agent = "critic"
        diagnosis = run_subagent(
            task=(
                "The coding workflow has failed repeatedly on the same step. "
                "Identify the most likely root cause and suggest one concrete "
                "fix the critic agent should consider."
            ),
            context=f"Current step: {current_step}\nLatest error: {error_message}\nCritic feedback so far: {critic_feedback}",
            session_id=state.get("session_id"),
        )
        planner_message = (
            "Planner Agent: Execution failed multiple times. Escalating workflow to Critic Agent for analysis.\n\n"
            f"Diagnostic subagent report:\n{diagnosis}"
        )
    elif not execution_success:
        next_agent = "coder"
        planner_message = (
            f"Planner Agent: Current Task: {current_step} Routing to Coder Agent for implementation."
        )
    else:
        next_agent = "critic"
        planner_message = (
            f"Planner Agent: Task '{current_step}' completed successfully. Sending generated solution to Critic Agent for evaluation."
        )

    return {
        "messages": messages + [AIMessage(content=planner_message)],
        "plan": plan,
        "current_step": current_step,
        "workflow_status": workflow_status,
        "next_agent": next_agent,
        "current_agent": "planner",
        "user_request": user_request,
    }
           