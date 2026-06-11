from typing import List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict

# Execution status

ExecutionStatus = Literal[
    "running",
    "success",
    "failed",
    "timeout",
    "crashed"
]

# Next agent options

NextAgent = Literal[
    "coder",
    "critic",
    "human",
    "end"
]

# Execution result schema

class ExecutionResult(BaseModel):
    """
    Structured execution result schema.
    """
    model_config = ConfigDict(extra="forbid")

    execution_status: ExecutionStatus = Field(
        ...,
        description="Final execution status."
    )

    execution_success: bool = Field(
        ...,
        description="Whether execution succeeded."
    )

    stdout: str = Field(
        default="",
        description="Standard output logs"
    )

    stderr: str = Field(
        default="",
        description="Standard error logs"
    )

    error_message: Optional[str] = Field(
        default=None,
        description="Execution error message."
    )

    executed_command: str= Field(
        ...,
        description="command executed inside sandbox."
    )

    generated_output_files: Optional[List[str]] = Field(
        default=None,
        description="Generated output artifacts."
    )

    execution_time: float= Field(
        ...,
        description="Execution duration in seconds."
    )

    next_agent: Literal["coder", "critic", "human"] = Field(
        ...,
        description="Next agent to route to after execution."
    )