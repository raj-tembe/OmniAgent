import logging
from langgraph.graph import END
from graph.edges import validate_transition


# router 

def route_workflow(state):
    """
    Central workflow router.

    Reads state["next_agent"]
    and returns the next graph node.
    Enforces retry limits and validates transitions.
    """

    # Check retry limit
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 5)
    if retry_count >= max_retries:
        logging.getLogger(__name__).warning(
            "Max retries (%d) reached. Ending workflow.", max_retries
        )
        return END

    next_agent = state.get(
        "next_agent",
        "end"
    )

    if not next_agent:

        return END

    if next_agent.lower() == "end":

        return END

    # Validate transition
    current_agent = state.get("current_agent", "")
    if not validate_transition(current_agent, next_agent):
        logging.getLogger(__name__).warning(
            "Unexpected transition from '%s' to '%s'", current_agent, next_agent
        )

    return next_agent


# route mapping

ROUTE_MAPPING = {

    "planner": "planner",

    "researcher": "researcher",

    "coder": "coder",

    "executor": "executor",

    "critic": "critic",

    "memory": "memory",

    "human": "human",

    "end": END
}