from langgraph.graph import (
    StateGraph,
    START,
    END
)

from graph.state import AgentState

from graph.nodes import (
    NODE_REGISTRY
)

from graph.conditional_edges import (
    register_conditional_edges
)

from graph.checkpoint import (
    graph_checkpoint
)


# create workflow graph

def create_workflow():
    """
    Build OMNIAGENT workflow graph.
    """

    workflow = StateGraph(
        AgentState
    )

    # register nodes

    for (
        node_name,
        node_function
    ) in NODE_REGISTRY.items():

        workflow.add_node(
            node_name,
            node_function
        )

    # entry point

    workflow.add_edge(
        START,
        "planner"
    )

    # conditional routing 

    workflow = (
        register_conditional_edges(
            workflow
        )
    )

    # compile graph

    graph = workflow.compile()

    return graph


# singleton workflow instance

omniagent_graph = create_workflow()