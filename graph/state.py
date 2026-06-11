from typing import List, Dict, Any
from langgraph.graph import MessagesState


class AgentState(MessagesState):

    # USER INPUT

    user_request: str = ""
    session_id: str = ""

    # PLANNING

    plan: List[str] = []
    current_step: str = ""
    completed_steps: List[str] = []

    # RESEARCH

    research_data: List[str] = []
    references: List[str] = []

    # CODE GENERATION

    project_name: str = ""
    generated_files: Dict[str, str] = {}

    # Example:
    # {
    #   "app.py": "...",
    #   "requirements.txt": "..."
    # }


    # EXECUTION

    execution_logs: str = ""
    execution_success: bool = False
    execution_output: str = ""

    # ERROR HANDLING

    error_message: str = ""
    retry_count: int = 0
    max_retries: int = 5

    # CRITIC / REVIEW

    critic_feedback: str = ""
    quality_score: float = 0.0
    security_issues: List[str] = []

    # HUMAN-IN-THE-LOOP

    approval_required: bool = False
    approved: bool = False
    human_feedback: str = ""

    # MEMORY

    memory_context: List[str] = []
    previous_attempts: List[Dict[str, Any]] = []

    # WORKFLOW CONTROL

    next_agent: str = ""
    workflow_status: str = ""
    current_agent: str = ""

    # OBSERVABILITY

    token_usage: int = 0
    execution_time: float = 0.0