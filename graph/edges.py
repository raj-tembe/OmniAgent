from langgraph.graph import END


# static edge 

GRAPH_EDGES = {

    "planner": [
        "researcher",
        "coder"
    ],

    "researcher": [
        "coder"
    ],

    "coder": [
        "executor"
    ],

    "executor": [
        "critic"
    ],

    "critic": [
        "memory"
    ],

    "memory": [
        END
    ]
}


# get next edges

def get_next_nodes(
    node_name: str
):
    """
    Returns possible next nodes.
    """

    return GRAPH_EDGES.get(
        node_name,
        []
    )


# validate edges 

def is_valid_transition(
    source: str,
    destination: str
):
    """
    Validates graph transition.
    """

    return (
        destination
        in GRAPH_EDGES.get(
            source,
            []
        )
    )