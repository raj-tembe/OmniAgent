"""
Event definitions for OmniAgent's internal event bus.

Every event that matters for the CLI, the future IDE, plugins, and the
permission engine is defined here as a typed pydantic model: a single stable
vocabulary of events that any number of subscribers (loggers, UI panels,
plugins) can listen to without the graph nodes knowing who's listening.
"""
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


#event type registry — every event's `type` field must be one of these

EventType = Literal[
    "session.started",
    "session.completed",
    "session.error",
    "agent.started",
    "agent.completed",
    "message.start",
    "message.delta",
    "message.end",
    "tool.call.start",
    "tool.call.end",
    "permission.requested",
    "permission.resolved",
]


#base event — every concrete event extends this

class Event(BaseModel):
    """
    Base shape shared by all bus events.
    """

    type: EventType = Field(
        ...,
        description="Discriminator identifying the event kind."
    )

    session_id: Optional[str] = Field(
        default=None,
        description="Session this event belongs to, if any."
    )

    timestamp: Optional[float] = Field(
        default=None,
        description="Unix timestamp the event was published at."
    )


# session lifecycle

class SessionStarted(Event):
    type: Literal["session.started"] = "session.started"
    user_request: str = Field(..., description="The task the session was started for.")


class SessionCompleted(Event):
    type: Literal["session.completed"] = "session.completed"
    execution_success: bool = Field(..., description="Whether the session finished successfully.")
    quality_score: Optional[float] = Field(default=None, description="Final critic quality score.")


class SessionError(Event):
    type: Literal["session.error"] = "session.error"
    error_message: str = Field(..., description="Error that terminated the session.")


#agent lifecycle (one per graph node execution)

class AgentStarted(Event):
    type: Literal["agent.started"] = "agent.started"
    agent: str = Field(..., description="Name of the agent/node starting.")


class AgentCompleted(Event):
    type: Literal["agent.completed"] = "agent.completed"
    agent: str = Field(..., description="Name of the agent/node that completed.")
    elapsed_seconds: Optional[float] = Field(default=None, description="Execution duration.")


#message streaming (LLM output)

class MessageStart(Event):
    type: Literal["message.start"] = "message.start"
    agent: str = Field(..., description="Agent producing the message.")


class MessageDelta(Event):
    type: Literal["message.delta"] = "message.delta"
    agent: str = Field(..., description="Agent producing the message.")
    text: str = Field(..., description="Incremental text chunk.")


class MessageEnd(Event):
    type: Literal["message.end"] = "message.end"
    agent: str = Field(..., description="Agent that finished producing the message.")


#tool calls

class ToolCallStart(Event):
    type: Literal["tool.call.start"] = "tool.call.start"
    tool: str = Field(..., description="Tool being invoked.")
    agent: str = Field(..., description="Agent invoking the tool.")
    args: Dict[str, Any] = Field(default_factory=dict, description="Arguments passed to the tool.")


class ToolCallEnd(Event):
    type: Literal["tool.call.end"] = "tool.call.end"
    tool: str = Field(..., description="Tool that finished executing.")
    agent: str = Field(..., description="Agent that invoked the tool.")
    success: bool = Field(..., description="Whether the tool call succeeded.")
    output: Optional[str] = Field(default=None, description="Truncated tool output.")


#permissions (Phase 1 will publish/consume these; defined now so the schema is stable)

class PermissionRequested(Event):
    type: Literal["permission.requested"] = "permission.requested"
    tool: str = Field(..., description="Tool requesting permission.")
    agent: str = Field(..., description="Agent requesting permission.")
    reason: Optional[str] = Field(default=None, description="Why approval is needed.")


class PermissionResolved(Event):
    type: Literal["permission.resolved"] = "permission.resolved"
    tool: str = Field(..., description="Tool the decision applies to.")
    decision: Literal["allow", "deny"] = Field(..., description="Resolution of the request.")


#convenience union for type checkers / handler signatures

AnyEvent = (
    SessionStarted
    | SessionCompleted
    | SessionError
    | AgentStarted
    | AgentCompleted
    | MessageStart
    | MessageDelta
    | MessageEnd
    | ToolCallStart
    | ToolCallEnd
    | PermissionRequested
    | PermissionResolved
)
