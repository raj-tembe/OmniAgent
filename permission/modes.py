"""
Built-in permission defaults for OmniAgent's two primary agent modes.

Two primary agent modes:
    - build: full access, nothing asks by default.
    - plan: read-only — file writes and code execution are denied outright
      rather than merely asked, since "plan" exists specifically for
      exploring/reviewing a codebase without side effects. A deny-by-default
      is the safer default for running fully LLM-generated code in a
      sandbox; users who want plan-mode-with-ask can still set it explicitly
      via `omniagent.json`.

These are defaults, not hard limits — `omniagent.json`'s `permission` block
and per-mode `agent.<mode>.permission` overrides both take precedence over
what's defined here (see permission/engine.py resolution order).
"""
from typing import Dict, Literal

from config.schema import PermissionAction

AgentMode = Literal["build", "plan"]

BUILTIN_MODE_DEFAULTS: Dict[str, Dict[str, PermissionAction]] = {
    "build": {},
    "plan": {
        "write": "deny",
        "edit": "deny",
        "bash": "deny",
    },
}

DEFAULT_MODE: AgentMode = "build"


def is_known_mode(mode: str) -> bool:
    return mode in BUILTIN_MODE_DEFAULTS
