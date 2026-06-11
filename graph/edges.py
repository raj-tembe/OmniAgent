from langgraph.graph import END


# static edge 

GRAPH_EDGES = {

    "planner": [
        "researcher",
        "coder",
        "human"
    ],

    "researcher": [
        "coder"
    ],

    "coder": [
        "executor"
    ],

    "executor": [
        "critic",
        "coder",
        "human"
    ],

    "critic": [
        "memory",
        "coder",
        "human"
    ],

    "memory": [
        END
    ],

    "human": [
        "coder",
        END
    ]
}


# validate transition

def validate_transition(source: str, destination: str) -> bool:
    """Returns True if the transition is explicitly defined OR destination is END."""
    if destination == END:
        return True
    return destination in GRAPH_EDGES.get(source, [])


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