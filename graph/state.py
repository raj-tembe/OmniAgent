from typing import List, Dict, Any
from langgraph.graph import MessagesState


class AgentState(MessagesState):

    # USER INPUT

    user_request: str = ""
    session_id: str = ""

    # PLANNING

    plan: List[str]
    current_step: str = ""
    completed_steps: List[str]

    # RESEARCH

    research_data: List[str]
    references: List[str]

    # CODE GENERATION

    generated_files: Dict[str, str]

    # Example:
    # {
    #   "app.py": "...",
    #   "requirements.txt": "..."
    # }


    # EXECUTION

    execution_logs: str = ""
    execution_success: bool
    execution_output: str = ""

    # ERROR HANDLING

    error_message: str = ""
    retry_count: int
    max_retries: int

    # CRITIC / REVIEW

    critic_feedback: str = ""
    quality_score: float
    security_issues: List[str]

    # HUMAN-IN-THE-LOOP

    approval_required: bool
    approved: bool
    human_feedback: str = ""

    # MEMORY

    memory_context: List[str]
    previous_attempts: List[Dict[str, Any]]

    # WORKFLOW CONTROL

    next_node: str = ""
    workflow_status: str = ""

    # OBSERVABILITY

    token_usage: int
    execution_time: float