"""
MCP (Model Context Protocol) client.

Wraps the official `mcp` SDK to connect to servers declared in
`omniagent.json`'s `mcp` block (see config/schema.py's McpServerConfig):
"local" servers are spawned as a subprocess over stdio, "remote" servers are
reached over SSE. Everything else in OmniAgent is synchronous, so these are
thin `asyncio.run(...)` wrappers around the SDK's async client — agent code
never has to know MCP itself is async under the hood.

Each connection is short-lived: connect, do one list/call, disconnect. MCP
servers (especially local ones spawned via npx) can be slow to start, so
this isn't the fastest possible design, but it's the simplest one that
doesn't leak subprocess/connection state across unrelated agent calls —
correctness over latency for a first implementation.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client

from config.schema import McpServerConfig

logger = logging.getLogger(__name__)


class McpError(Exception):
    """Raised when connecting to or calling an MCP server fails."""


def _tool_to_dict(tool) -> Dict[str, Any]:
    return {
        "name": tool.name,
        "description": tool.description or "",
        "input_schema": tool.inputSchema,
    }


async def _with_session(server: McpServerConfig, work):
    """
    Connect to `server` (stdio for local, SSE for remote), initialize an MCP
    session, run `work(session)`, then tear the connection down. Shared by
    list_tools/call_tool so both go through identical connection handling.
    """
    if server.type == "local":
        if not server.command:
            raise McpError("Local MCP server config is missing 'command'.")

        params = StdioServerParameters(command=server.command[0], args=list(server.command[1:]))
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await work(session)

    elif server.type == "remote":
        if not server.url:
            raise McpError("Remote MCP server config is missing 'url'.")

        async with sse_client(server.url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await work(session)

    else:
        raise McpError(f"Unknown MCP server type: {server.type!r}")


async def _list_tools_async(server: McpServerConfig) -> List[Dict[str, Any]]:
    async def work(session: ClientSession):
        result = await session.list_tools()
        return [_tool_to_dict(t) for t in result.tools]

    return await _with_session(server, work)


async def _call_tool_async(server: McpServerConfig, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    async def work(session: ClientSession):
        result = await session.call_tool(tool_name, arguments)
        text_parts = [block.text for block in result.content if hasattr(block, "text")]
        return {
            "success": not result.isError,
            "content": "\n".join(text_parts),
        }

    return await _with_session(server, work)


def list_tools(server: McpServerConfig, timeout: float = 30.0) -> List[Dict[str, Any]]:
    """
    List tools exposed by `server`. Raises McpError on connection/protocol
    failure — callers doing multi-server discovery should catch this per
    server (see mcp_client/registry.py) so one broken server doesn't block
    discovery of the rest.
    """
    try:
        return asyncio.run(asyncio.wait_for(_list_tools_async(server), timeout=timeout))
    except asyncio.TimeoutError as e:
        raise McpError(f"Timed out listing tools after {timeout}s.") from e
    except McpError:
        raise
    except Exception as e:
        raise McpError(f"Failed to list tools: {e}") from e


def call_tool(server: McpServerConfig, tool_name: str, arguments: Dict[str, Any], timeout: float = 60.0) -> Dict[str, Any]:
    """
    Call `tool_name` on `server` with `arguments`. Returns a dict rather than
    raising for tool-level failures (the tool ran but reported an error),
    matching the success/error dict convention every other tool in
    tools/code_tools and tools/agent_tools already follows — only connection
    and protocol failures raise McpError.
    """
    try:
        return asyncio.run(asyncio.wait_for(_call_tool_async(server, tool_name, arguments), timeout=timeout))
    except asyncio.TimeoutError as e:
        raise McpError(f"Timed out calling tool '{tool_name}' after {timeout}s.") from e
    except McpError:
        raise
    except Exception as e:
        raise McpError(f"Failed to call tool '{tool_name}': {e}") from e
