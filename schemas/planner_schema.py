from typing import List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict

#workflow status options

workflowstatus = Literal[
    "planning",
    "researching",
    "coding",
    "executing",
    "reviewing",
    "failed",
    "completed"
]

#next agent options
NextAgent = Literal[
    "researcher",
    "coder",
    "executor",
    "critic",
    "human",
    "end"
]

#planner output schema  

class PlannerOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """
    Structured output schema for Planner Agent.

    This schema ensures:
    - deterministic planning outputs
    - reliable routing
    - workflow consistency
    - safer LangGraph execution
    """

    #execution plan
    tasks: List[str] = Field(
        ...,
        description=(
            "Step-by-step actionable execution plan"
            "for completing the user's request."
    ),
    examples=[
        [
             "Create FastAPI project structure",
            "Implement JWT authentication",
            "Add database models",
            "Write API endpoints",
            "Create tests"

        ]
            ]
    )

    #current execution step
    current_step: str = Field(
        ...,
        description=(
            "the current workflow step being executed."
    ),
        examples=[
            "Implement JWT authentication"
        ]
    )

    #workflow status
    workflow_status: workflowstatus = Field(
        ...,
        description=(
            "the current overall workflow phase."
        ),
        examples=[
            "coding"
        ]
    )

    #optioal planner reasoning
    reasoning: Optional[str] = Field(
        default=None,
        description=(
            "Optional explanation for why the planner "
            "selected the current step and next agent."
        ),
        examples=[
            "Execution has not started yet,"
            "so the workflow should proceed"
            "to the coding Agent."
        ]
    )

    #next agent selection
    next_agent: NextAgent = Field(
        ...,
        description=(
            "The next agent the workflow should route to."
        ),
        examples=[
            "coder"
        ]
    )

    #retry / recovery strategy
    recovery_strategy: Optional[str] = Field(
        default=None,
        description=(
            "Optional recovery or retry strategy "
            "if previous execution failed."
        ),
        examples=[
            "Retry code generation with corrected imports"
            "and dependencies handling."
        ]
    )

    #human intervention flag
    require_human_approval: bool = Field(
        default=False,
        description=(
            "Whether the workflow should pause "
            "for human approval or intervention."
        ),
        examples=[
            False
        ]
    )
