from langgraph.graph import (
    StateGraph,
    START,
    END
)
import time

from graph.state import AgentState

from graph.nodes import (
    NODE_REGISTRY
)

from graph.conditional_edges import (
    register_conditional_edges
)

from graph.checkpoint import GraphCheckpointManager
from observability.metrics import metrics_tracker
from observability.monitoring import system_monitor


class OmniAgentCallbacks:
    """LangGraph callbacks for metrics and monitoring."""

    def on_chain_start(self, serialized, inputs, **kwargs):
        self._start = time.time()
        agent = serialized.get("name", "unknown")
        system_monitor.info(agent, f"Agent started: {agent}")
        metrics_tracker.record_agent_execution(agent)

    def on_chain_end(self, outputs, **kwargs):
        elapsed = time.time() - getattr(self, "_start", time.time())
        system_monitor.info("workflow", f"Step completed in {elapsed:.2f}s")

    def on_chain_error(self, error, **kwargs):
        system_monitor.error("workflow", str(error))


# Initialize checkpoint manager
graph_checkpoint = GraphCheckpointManager()


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

    # compile graph with checkpointer

    graph = workflow.compile(
        checkpointer=graph_checkpoint.checkpointer
    )

    return graph


# singleton workflow instance

omniagent_graph = create_workflow()