from langgraph.graph import END

from graph.router import (
    route_workflow
)


# conditional edge map

CONDITIONAL_EDGE_MAP = {

    "planner": "planner",

    "researcher": "researcher",

    "coder": "coder",

    "executor": "executor",

    "critic": "critic",

    "memory": "memory",

    "human": "human",

    END: END
}


# register conditional edges

def register_conditional_edges(
    workflow
):
    """
    Register routing logic
    for all workflow nodes.
    """

    workflow.add_conditional_edges(

        "planner",

        route_workflow,

        CONDITIONAL_EDGE_MAP
    )

    workflow.add_conditional_edges(

        "researcher",

        route_workflow,

        CONDITIONAL_EDGE_MAP
    )

    workflow.add_conditional_edges(

        "coder",

        route_workflow,

        CONDITIONAL_EDGE_MAP
    )

    workflow.add_conditional_edges(

        "executor",

        route_workflow,

        CONDITIONAL_EDGE_MAP
    )

    workflow.add_conditional_edges(

        "critic",

        route_workflow,

        CONDITIONAL_EDGE_MAP
    )

    workflow.add_conditional_edges(

        "memory",

        route_workflow,

        CONDITIONAL_EDGE_MAP
    )

    workflow.add_conditional_edges(

        "human",

        route_workflow,

        CONDITIONAL_EDGE_MAP
    )

    return workflow
