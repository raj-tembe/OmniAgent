from typing import List, Dict, Any

from langgraph.graph import MessagesState


class AgentState(MessagesState):
    """Workflow state for OmniAgent.

    TypedDict does not provide runtime defaults, so callers must read with
    state.get(key, default) or populate fields explicitly when a node first
    introduces them.
    """

    # USER INPUT

    user_request: str
    session_id: str

    # PLANNING

    plan: List[str]
    current_step: str
    completed_steps: List[str]

    # RESEARCH

    research_data: List[Any]
    research_status: str
    research_summary: str
    research_sources: List[Any]
    references: List[str]
    implementation_recommendations: str
    recommended_technologies: List[str]
    security_considerations: List[str]
    performance_considerations: List[str]
    architecture_suggestions: List[str]

    # CODE GENERATION

    project_name: str
    generated_files: Dict[str, str]
    entry_point: str
    coding_status: str
    coding_explanation: str

    # EXECUTION

    execution_logs: str
    execution_success: bool
    execution_output: str
    execution_status: str
    execution_time: float

    # ERROR HANDLING

    error_message: str
    retry_count: int
    max_retries: int

    # CRITIC / REVIEW

    review_status: str
    critic_feedback: str
    critic_summary: str
    quality_score: float
    review_issues: List[Any]
    security_issues: List[str]
    improvement_suggestions: List[str]

    # HUMAN-IN-THE-LOOP

    approval_required: bool
    approved: bool
    human_feedback: str
    interactive: bool

    # MEMORY

    memory_context: List[str]
    memory_type: str
    memory_stats: Dict[str, Any]
    previous_attempts: List[Dict[str, Any]]
    similar_failures: List[Any]

    # WORKFLOW CONTROL

    next_agent: str
    workflow_status: str
    current_agent: str

    # OBSERVABILITY

    token_usage: int