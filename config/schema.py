"""
Schema for OmniAgent's declarative config file (`omniagent.json`).

One config file shape covering permissions, providers, agents, MCP servers,
and plugins. Later phases wire `permission` into an actual enforcement
engine; `provider` into the provider abstraction; for now this just defines
the shape and a loader so every later phase reads/writes the same format
instead of inventing a new one per feature.

Env vars in config/env.py remain the source of truth for secrets (API keys).
This file is for everything else: policy and wiring, safe to commit to a repo.
"""
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


#permission actions — tool call outcomes

PermissionAction = Literal["allow", "ask", "deny"]


class PermissionConfig(BaseModel):
    """
    Per-tool permission rules. Keys are tool names or wildcard patterns
    (e.g. "bash", "edit", "mymcp_*"); "*" matches everything not otherwise
    matched. Consumed by the Phase 1 permission engine.
    """

    rules: Dict[str, PermissionAction] = Field(
        default_factory=dict,
        description="Tool name (or wildcard) -> allow/ask/deny."
    )

    auto: bool = Field(
        default=False,
        description="Auto-approve mode: approve 'ask' rules automatically. Explicit 'deny' rules are still enforced."
    )


#agent modes — Phase 1 builds the enforcement; this just names them

AgentMode = Literal["build", "plan"]


class AgentModeConfig(BaseModel):
    """
    Configuration for one primary agent mode (build/plan-equivalent).
    """

    mode: AgentMode = Field(..., description="Which built-in mode this profile is based on.")

    permission: Optional[PermissionConfig] = Field(
        default=None,
        description="Mode-specific permission overrides layered on top of the top-level permission config."
    )

    model: Optional[str] = Field(
        default=None,
        description="Model override for this mode, if different from the default provider model."
    )


#providers

class ProviderConfig(BaseModel):
    """
    One configured LLM provider entry. Actual credentials stay in env vars
    (config/env.py); this just says which providers are enabled and which
    model each defaults to, so Phase 2's provider abstraction has one place
    to read a declarative catalog from.
    """

    model: Optional[str] = Field(default=None, description="Default model id for this provider.")
    enabled: bool = Field(default=True, description="Whether this provider is available for selection.")


#MCP servers

class McpServerConfig(BaseModel):
    """
    One configured MCP server (local command or remote URL).
    """

    type: Literal["local", "remote"] = Field(..., description="Whether this server is spawned locally or accessed over HTTP.")
    command: Optional[List[str]] = Field(default=None, description="Command + args to launch a local MCP server.")
    url: Optional[str] = Field(default=None, description="URL for a remote MCP server.")
    enabled: bool = Field(default=True, description="Whether this MCP server is active.")


#top-level config

class OmniAgentConfig(BaseModel):
    """
    Root shape of `omniagent.json`.
    """

    schema_: Optional[str] = Field(default=None, alias="$schema", description="JSON schema URL for editor validation.")

    permission: PermissionConfig = Field(
        default_factory=PermissionConfig,
        description="Top-level tool permission rules."
    )

    agent: Dict[str, AgentModeConfig] = Field(
        default_factory=dict,
        description="Named agent mode profiles (e.g. 'build', 'plan')."
    )

    provider: Dict[str, ProviderConfig] = Field(
        default_factory=dict,
        description="Configured LLM providers, keyed by provider name."
    )

    mcp: Dict[str, McpServerConfig] = Field(
        default_factory=dict,
        description="Configured MCP servers, keyed by server name."
    )

    plugin: List[str] = Field(
        default_factory=list,
        description="npm-style plugin package names or local plugin paths to load."
    )

    model_config = {"populate_by_name": True}
