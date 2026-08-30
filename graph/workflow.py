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
from bus import bus, AgentStarted, AgentCompleted, SessionError


class OmniAgentCallbacks:
    """LangGraph callbacks for metrics, monitoring, and the event bus.

    Every node in NODE_REGISTRY runs as its own LangChain "chain", so
    on_chain_start/on_chain_end fire once per agent step — that's what lets
    this publish AgentStarted/AgentCompleted on the bus without touching each
    agent file individually. Anything subscribing to the bus (a future
    logger, the IDE's live panel, the Phase 1 permission engine) gets
    per-agent visibility for free.
    """

    raise_error = False
    ignore_chain = False
    ignore_agent = False
    ignore_llm = False
    ignore_chat_model = False

    def __init__(self, session_id: str | None = None):
        self.session_id = session_id

    def on_chain_start(self, serialized, inputs, **kwargs):
        try:
            self._start = time.time()
            agent = (serialized or {}).get("name", "unknown") if isinstance(serialized, dict) else "unknown"
            self._current_agent = agent
            system_monitor.info(agent, f"Agent started: {agent}")
            metrics_tracker.record_agent_execution(agent)
            bus.publish(AgentStarted(agent=agent, session_id=self.session_id))
        except Exception:
            return None

    def on_chain_end(self, outputs, **kwargs):
        try:
            elapsed = time.time() - getattr(self, "_start", time.time())
            system_monitor.info("workflow", f"Step completed in {elapsed:.2f}s")
            agent = getattr(self, "_current_agent", "unknown")
            bus.publish(AgentCompleted(agent=agent, elapsed_seconds=elapsed, session_id=self.session_id))
        except Exception:
            return None

    def on_chain_error(self, error, **kwargs):
        try:
            system_monitor.error("workflow", str(error))
            bus.publish(SessionError(error_message=str(error), session_id=self.session_id))
        except Exception:
            return None

    def on_chat_model_start(self, serialized, messages, **kwargs):
        return None

    def on_llm_end(self, response, **kwargs):
        return None

    def on_llm_error(self, error, **kwargs):
        return None


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