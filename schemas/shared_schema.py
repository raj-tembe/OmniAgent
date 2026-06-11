from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict


#common workflow status

WorkflowStatus = Literal[
    "planning",
    "researching",
    "coding",
    "executing",
    "reviewing",
    "completed",
    "failed",
    "paused"
]


#common agent types

AgentType = Literal[
    "planner",
    "researcher",
    "coder",
    "executor",
    "critic",
    "human",
    "end"
]


#log level

LogLevel = Literal[
    "info",
    "warning",
    "error",
    "critical"
]


#execution priority 

PriorityLevel = Literal[
    "low",
    "medium",
    "high",
    "critical"
]


#workflow message

class WorkflowMessage(BaseModel):
    """
    Standard workflow communication message.
    """

    agent: AgentType = Field(
        ...,
        description="Agent generating the message."
    )

    message: str = Field(
        ...,
        description="Workflow message content."
    )

    level: LogLevel = Field(
        default="info",
        description="Message severity level."
    )

    timestamp: Optional[str] = Field(
        default=None,
        description="Message timestamp."
    )


#execution log

class ExecutionLog(BaseModel):
    """
    Standardized execution log entry.
    """

    step: str = Field(
        ...,
        description="Workflow step name."
    )

    status: WorkflowStatus = Field(
        ...,
        description="Execution status."
    )

    agent: AgentType = Field(
        ...,
        description="Responsible agent."
    )

    details: Optional[str] = Field(
        default=None,
        description="Execution details/logs."
    )

    execution_time: Optional[float] = Field(
        default=None,
        description="Execution duration."
    )


#generated artifact

class GeneratedArtifact(BaseModel):
    """
    Represents generated project artifacts.
    """

    filename: str = Field(
        ...,
        description="Artifact filename/path."
    )

    content_type: str = Field(
        ...,
        description="Artifact content type."
    )

    description: Optional[str] = Field(
        default=None,
        description="Artifact purpose."
    )


#security issue

class SecurityIssue(BaseModel):
    """
    Represents detected security problems.
    """

    title: str = Field(
        ...,
        description="Security issue title."
    )

    severity: PriorityLevel = Field(
        ...,
        description="Security severity level."
    )

    description: str = Field(
        ...,
        description="Detailed issue description."
    )

    recommendation: str = Field(
        ...,
        description="Suggested remediation."
    )


#improvement suggestion
class ImprovementSuggestion(BaseModel):
    """
    Standard improvement recommendation.
    """

    category: str = Field(
        ...,
        description="Improvement category."
    )

    suggestion: str = Field(
        ...,
        description="Improvement recommendation."
    )

    impact: PriorityLevel = Field(
        default="medium",
        description="Expected impact level."
    )


#memory entry

class MemoryEntry(BaseModel):
    """
    Long-term memory representation.
    """

    memory_type: str = Field(
        ...,
        description="Type of stored memory."
    )

    content: str = Field(
        ...,
        description="Memory content."
    )

    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional memory metadata."
    )


#tool execution result

class ToolExecutionResult(BaseModel):
    """
    Standardized tool execution response.
    """

    tool_name: str = Field(
        ...,
        description="Executed tool name."
    )

    success: bool = Field(
        ...,
        description="Whether tool execution succeeded."
    )

    output: Optional[str] = Field(
        default=None,
        description="Tool output."
    )

    error: Optional[str] = Field(
        default=None,
        description="Tool execution error."
    )

    execution_time: Optional[float] = Field(
        default=None,
        description="Tool execution duration."
    )


#workflow checkpoint 

class WorkflowCheckpoint(BaseModel):
    """
    Workflow persistence checkpoint.
    """

    checkpoint_id: str = Field(
        ...,
        description="Unique checkpoint identifier."
    )

    workflow_status: WorkflowStatus = Field(
        ...,
        description="Workflow state at checkpoint."
    )

    active_agent: AgentType = Field(
        ...,
        description="Currently active agent."
    )

    retry_count: int = Field(
        default=0,
        description="Current retry count."
    )

    state_snapshot: Dict[str, Any] = Field(
        ...,
        description="Serialized workflow state."
    )


#human approval request

class HumanApprovalRequest(BaseModel):
    """
    Human approval workflow model.
    """

    reason: str = Field(
        ...,
        description="Reason approval is required."
    )

    requested_by: AgentType = Field(
        ...,
        description="Agent requesting approval."
    )

    risk_level: PriorityLevel = Field(
        ...,
        description="Risk severity level."
    )

    recommended_action: Optional[str] = Field(
        default=None,
        description="Suggested human action."
    )


#agent metadata

class AgentMetadata(BaseModel):
    """
    Metadata about workflow agents.
    """

    agent_name: AgentType = Field(
        ...,
        description="Agent identifier."
    )

    description: str = Field(
        ...,
        description="Agent responsibilities."
    )

    capabilities: List[str] = Field(
        ...,
        description="Agent capabilities."
    )

    enabled_tools: Optional[List[str]] = Field(
        default=None,
        description="Tools available to the agent."
    )