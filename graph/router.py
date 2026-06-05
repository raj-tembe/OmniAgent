from langgraph.graph import END


# router 

def route_workflow(state):
    """
    Central workflow router.

    Reads state["next_agent"]
    and returns the next graph node.
    """

    next_agent = state.get(
        "next_agent",
        "end"
    )

    if not next_agent:

        return END

    if next_agent.lower() == "end":

        return END

    return next_agent


# route mapping

ROUTE_MAPPING = {

    "planner": "planner",

    "researcher": "researcher",

    "coder": "coder",

    "executor": "executor",

    "critic": "critic",

    "memory": "memory",

    "end": END
}