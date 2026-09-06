"""
Shared factory for constructing a `PermissionEngine` that knows about server
mode — every call site (executor_agent.py, mcp_client/registry.py, and
whatever calls a permission-gated tool next) needs the exact same "use the
HTTP resolver instead of a terminal prompt when running under
server/sessions.py" logic. Kept in one place instead of duplicated per
call site, which is how this drifted the first time: executor_agent.py grew
its own local copy before this existed.
"""
from typing import Optional

from config import load_config
from config.schema import OmniAgentConfig
from permission.engine import PermissionEngine
from permission.modes import DEFAULT_MODE


def build_permission_engine(
    agent_mode: str = DEFAULT_MODE,
    interactive: bool = False,
    server_mode: bool = False,
    config: Optional[OmniAgentConfig] = None,
) -> PermissionEngine:
    """
    Build a PermissionEngine for `agent_mode`. When `server_mode` is True,
    "ask" rules resolve through server/permission_bridge.py's HTTP
    round-trip instead of a terminal prompt — deferred import, since
    callers that never run under server mode (the plain CLI) shouldn't need
    FastAPI installed at all.

    `config` defaults to `load_config()` (the merged global/project
    omniagent.json) if not given — pass the config a caller already has in
    hand (e.g. mcp_client/registry.py's callers already loaded one to look
    up MCP servers) to avoid loading it twice and to guarantee both use the
    exact same rules.
    """
    if config is None:
        config = load_config()

    resolver = None
    if server_mode:
        from server.permission_bridge import make_server_resolver
        resolver = make_server_resolver()

    return PermissionEngine(config, mode=agent_mode, interactive=interactive, resolver=resolver)
