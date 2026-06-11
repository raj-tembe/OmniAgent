"""Purpose
Core planner logic.

Responsibility
analyze user goal
break tasks
prioritize execution steps"""

from typing import Dict, List
from langchain_core.messages import AIMessage
from graph.state import AgentState
from agents.planner.planner_chain import create_planner_chain

def planner_agent(state: AgentState) -> Dict:
    """
    Planner Agent

    Responsibilities:
    - Understand user goal
    - Break task into actionable steps
    - Decide current workflow phase
    - Route execution to next agent
    """
        
    messages = state.get("messages", [])
    user_request = state.get(
        "user_request",
        messages[-1].content if messages else "No request provided."
    )

    plan = bool(state.get("plan", []))
    completed_steps = bool(state.get("completed_steps", []))
    retry_count = state.get("retry_count", 0)
    execution_success = state.get("execution_success", False)
    critic_feedback = state.get("critic_feedback", "")
    error_message = state.get("error_message", "")

    # Planner Chain
    planner_chain = create_planner_chain()

    # Generate Plan
    response = planner_chain.invoke({
        "user_request": user_request,
        "existing_plan": plan,
        "completed_steps": completed_steps,
        "retry_count": retry_count,
        "execution_success": execution_success,
        "critic_feedback": critic_feedback,
        "error_message": error_message,
    })

    # extract structured planner output
    plan = response.tasks
    current_step = response.current_step
    workflow_status = response.workflow_status
    next_agent = response.next_agent

    # routing logic based on workflow status
    if workflow_status == "completed":

        next_agent = "end"

        planner_message = (
            "Planner Agent: "
            "Workflow planning and execution completed successfully."
        )

    #execution failed multiple times, route to critic for review
    elif retry_count >= 3:
        
        next_agent = "critic"

        planner_message = (
            "Planner Agent: "
            "Execution failed multiple times. "
            "Escalating workflow to Critic Agent for anlysis."
        )

    # normal coding flow, route to coder
    elif not execution_success:

        next_agent = "coder"

        planner_message = (
            f"Planner Agent: "
            f"Current Task: {current_step}"
            f"Routing to Coder Agent for implementation."
        )

    # execution succeeded
    else:

        next_agent = "critic"

        planner_message = (
            f"Planner Agent: "
            f"Task '{current_step}' completed successfully. "
            f"Sending generated solution to Critic Agent for evaluation."
        )

    # return updated state
    return {

        #conversation history
        "messages": messages + [AIMessage(content=planner_message)],

        #planner output
        "plan": plan,
        "current_step": current_step,

        #workflow
        "workflow_status": workflow_status,
        "next_agent": next_agent,
        "current_agent": "planner",

        #user goal
        "user_request": user_request,
    }
           