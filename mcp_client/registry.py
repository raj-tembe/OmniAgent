"""
MCP server registry.

Ties three things together: the `mcp` block of `omniagent.json`
(config/schema.py's McpServerConfig), the low-level client
(mcp_client/client.py), and the permission engine (permission/engine.py).

MCP tool calls are gated by the permission engine the same way built-in
tools are, using the `<server>_<tool>` naming convention documented in
config/schema.py's PermissionConfig ("mymcp_*" wildcard rules match this
shape) — an MCP tool call is exactly as capable of doing something dangerous
as a built-in one, so it doesn't get a free pass. The gate is not optional:
`call_server_tool` always checks, building a PermissionEngine via
permission.factory when the caller doesn't hand one in — same server-mode
awareness executor_agent.py gets, so a future agent wiring MCP tools in
doesn't have to rediscover that plumbing.
"""
import logging
from typing import Any, Dict, List, Optional

from config.schema import OmniAgentConfig
from mcp_client.client import McpError, call_tool, list_tools
from permission import DEFAULT_MODE, PermissionDenied, PermissionEngine, build_permission_engine

logger = logging.getLogger(__name__)


def enabled_servers(config: OmniAgentConfig) -> Dict[str, Any]:
    """Every MCP server in `config.mcp` with `enabled=True`."""
    return {name: server for name, server in config.mcp.items() if server.enabled}


def discover_all_tools(config: OmniAgentConfig) -> Dict[str, List[Dict[str, Any]]]:
    """
    List tools from every enabled MCP server. A server that fails to connect
    is logged and skipped rather than aborting discovery for the others —
    one misconfigured server shouldn't take every other one down, the same
    principle bus/event_bus.py applies to broken subscribers.
    """
    results: Dict[str, List[Dict[str, Any]]] = {}

    for name, server in enabled_servers(config).items():
        try:
            results[name] = list_tools(server)
        except McpError as e:
            logger.warning("Could not list tools for MCP server '%s': %s", name, e)
            results[name] = []

    return results


def call_server_tool(
    config: OmniAgentConfig,
    server_name: str,
    tool_name: str,
    arguments: Dict[str, Any],
    permission_engine: Optional[PermissionEngine] = None,
    agent: str = "",
    agent_mode: str = DEFAULT_MODE,
    interactive: bool = False,
    server_mode: bool = False,
) -> Dict[str, Any]:
    """
    Call `tool_name` on the MCP server named `server_name`, gated by a
    permission check on "<server_name>_<tool_name>" (matching the wildcard
    convention in omniagent.json's permission rules).

    Pass `permission_engine` explicitly to reuse one an agent already
    built (e.g. so the same engine instance gates both a built-in tool call
    and an MCP one in the same step). Otherwise one is built automatically
    from `config`, `agent_mode`, `interactive`, and `server_mode` — the same
    server-mode-aware construction executor_agent.py uses, via
    permission.factory.build_permission_engine, so "ask" rules resolve
    through the desktop app's approval dialog in server mode instead of a
    terminal prompt that has nowhere to go.

    Returns a success/error dict for anything that isn't an outright
    permission denial, consistent with every other tool wrapper in this
    codebase; a denial returns success=False with a clear reason rather than
    raising, so a calling agent can route around it instead of crashing.
    """
    servers = enabled_servers(config)
    if server_name not in servers:
        return {"success": False, "error": f"MCP server '{server_name}' is not configured or not enabled."}

    if permission_engine is None:
        permission_engine = build_permission_engine(
            agent_mode=agent_mode, interactive=interactive, server_mode=server_mode, config=config,
        )

    permission_tool_name = f"{server_name}_{tool_name}"

    if not permission_engine.check(permission_tool_name, agent=agent, reason=f"Call MCP tool {tool_name} on {server_name}."):
        return {"success": False, "error": f"Permission denied for MCP tool '{permission_tool_name}'."}

    try:
        return call_tool(servers[server_name], tool_name, arguments)
    except McpError as e:
        return {"success": False, "error": str(e)}
