"""
Permission engine.

Central place that decides whether a tool call (running generated code,
writing a file, etc.) is allowed to proceed: per-tool allow/ask/deny rules,
wildcard patterns, an --auto mode, and mode-aware defaults (build vs plan).

Resolution order, lowest to highest precedence:
    1. built-in mode defaults (permission/modes.py)
    2. top-level `permission.rules` in omniagent.json
    3. `agent.<mode>.permission.rules` in omniagent.json (mode-specific override)

A rule can be an exact tool name ("bash"), a wildcard ("mymcp_*"), or the
catch-all "*". Exact match wins over wildcard; the first matching wildcard
(in insertion order) wins over "*". Anything with no matching rule at all
defaults to "allow" — a fresh install isn't unexpectedly locked down.
"""
import fnmatch
import logging
import sys
from typing import Callable, Dict, Optional

from bus import bus, PermissionRequested, PermissionResolved
from config.schema import OmniAgentConfig, PermissionAction
from permission.modes import BUILTIN_MODE_DEFAULTS, DEFAULT_MODE

logger = logging.getLogger(__name__)


class PermissionDenied(Exception):
    """Raised when a tool call is blocked by a deny rule (or a declined ask)."""

    def __init__(self, tool: str, reason: Optional[str] = None):
        self.tool = tool
        self.reason = reason
        message = f"Permission denied for tool '{tool}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)


def resolve_rules(config: OmniAgentConfig, mode: str) -> Dict[str, PermissionAction]:
    """
    Merge built-in mode defaults, top-level config, and mode-specific config
    into the final tool -> action mapping used for this mode.
    """
    rules: Dict[str, PermissionAction] = dict(BUILTIN_MODE_DEFAULTS.get(mode, {}))
    rules.update(config.permission.rules)

    mode_config = config.agent.get(mode)
    if mode_config is not None and mode_config.permission is not None:
        rules.update(mode_config.permission.rules)

    return rules


def resolve_auto(config: OmniAgentConfig, mode: str) -> bool:
    """Whether auto-approve is active for this mode."""
    mode_config = config.agent.get(mode)
    if mode_config is not None and mode_config.permission is not None:
        return mode_config.permission.auto
    return config.permission.auto


def _match_rule(tool: str, rules: Dict[str, PermissionAction]) -> PermissionAction:
    if tool in rules:
        return rules[tool]

    for pattern, action in rules.items():
        if pattern == "*":
            continue
        if fnmatch.fnmatch(tool, pattern):
            return action

    if "*" in rules:
        return rules["*"]

    return "allow"


#default prompt for interactive "ask" resolution — swappable for tests / a
#future IDE prompt without touching the engine's control flow.
def _default_prompt(tool: str, agent: str, reason: Optional[str]) -> bool:
    print(f"\n[PERMISSION REQUIRED] {agent} wants to use '{tool}'.")
    if reason:
        print(f"Reason: {reason}")
    answer = input("Allow? (y/n): ").strip().lower()
    return answer == "y"


class PermissionEngine:
    """
    Evaluates and enforces permission rules for a single agent mode.
    """

    def __init__(
        self,
        config: OmniAgentConfig,
        mode: str = DEFAULT_MODE,
        interactive: bool = False,
        prompt: Callable[[str, str, Optional[str]], bool] = _default_prompt,
    ):
        self.config = config
        self.mode = mode
        self.interactive = interactive
        self.prompt = prompt
        self.rules = resolve_rules(config, mode)
        self.auto = resolve_auto(config, mode)

    def evaluate(self, tool: str) -> PermissionAction:
        """Return the raw allow/ask/deny rule for `tool`, before auto-mode is applied."""
        return _match_rule(tool, self.rules)

    def check(self, tool: str, agent: str = "", reason: Optional[str] = None, session_id: Optional[str] = None) -> bool:
        """
        Decide whether `tool` may run right now. Publishes
        PermissionRequested/Resolved on the bus for anything that isn't a
        plain allow, so a future IDE panel or logger can show what happened
        without polling.

        Returns True/False rather than raising — call sites decide how to
        route the workflow on denial (e.g. executor_agent routes to
        "human" or emits an error message instead of crashing the graph).
        """
        action = self.evaluate(tool)

        if action == "deny":
            bus.publish(PermissionRequested(tool=tool, agent=agent, reason=reason, session_id=session_id))
            bus.publish(PermissionResolved(tool=tool, decision="deny", session_id=session_id))
            logger.info("Permission denied for tool '%s' (mode=%s)", tool, self.mode)
            return False

        if action == "allow":
            return True

        # action == "ask"
        if self.auto:
            logger.info("Auto-approving 'ask' rule for tool '%s' (mode=%s, --auto)", tool, self.mode)
            bus.publish(PermissionRequested(tool=tool, agent=agent, reason=reason, session_id=session_id))
            bus.publish(PermissionResolved(tool=tool, decision="allow", session_id=session_id))
            return True

        bus.publish(PermissionRequested(tool=tool, agent=agent, reason=reason, session_id=session_id))

        if self.interactive and sys.stdin.isatty():
            approved = self.prompt(tool, agent, reason)
        else:
            logger.info(
                "Non-interactive environment — denying 'ask' rule for tool '%s' by default.", tool
            )
            approved = False

        bus.publish(PermissionResolved(tool=tool, decision="allow" if approved else "deny", session_id=session_id))
        return approved
