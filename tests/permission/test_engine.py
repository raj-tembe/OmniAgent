import unittest
from unittest.mock import patch

from bus.event_bus import EventBus, WILDCARD
import permission.engine as engine_module
from config.schema import AgentModeConfig, OmniAgentConfig, PermissionConfig
from permission.engine import PermissionDenied, PermissionEngine, resolve_auto, resolve_rules
from permission.modes import BUILTIN_MODE_DEFAULTS


class TestResolveRules(unittest.TestCase):

    def test_build_mode_has_no_builtin_restrictions(self):
        rules = resolve_rules(OmniAgentConfig(), "build")
        self.assertEqual(rules, {})

    def test_plan_mode_denies_write_edit_bash_by_default(self):
        rules = resolve_rules(OmniAgentConfig(), "plan")
        self.assertEqual(rules["write"], "deny")
        self.assertEqual(rules["edit"], "deny")
        self.assertEqual(rules["bash"], "deny")

    def test_top_level_config_overrides_builtin_mode_default(self):
        cfg = OmniAgentConfig(permission=PermissionConfig(rules={"bash": "ask"}))
        rules = resolve_rules(cfg, "plan")
        self.assertEqual(rules["bash"], "ask")
        # unrelated builtin default untouched
        self.assertEqual(rules["write"], "deny")

    def test_mode_specific_config_overrides_top_level(self):
        cfg = OmniAgentConfig(
            permission=PermissionConfig(rules={"bash": "ask"}),
            agent={"plan": AgentModeConfig(mode="plan", permission=PermissionConfig(rules={"bash": "allow"}))},
        )
        rules = resolve_rules(cfg, "plan")
        self.assertEqual(rules["bash"], "allow")

    def test_resolve_auto_prefers_mode_specific(self):
        cfg = OmniAgentConfig(
            permission=PermissionConfig(auto=False),
            agent={"build": AgentModeConfig(mode="build", permission=PermissionConfig(auto=True))},
        )
        self.assertTrue(resolve_auto(cfg, "build"))
        self.assertFalse(resolve_auto(cfg, "plan"))


class TestPermissionEngineEvaluate(unittest.TestCase):

    def test_exact_match_wins_over_wildcard(self):
        cfg = OmniAgentConfig(permission=PermissionConfig(rules={"mymcp_*": "ask", "mymcp_search": "allow"}))
        engine = PermissionEngine(cfg, mode="build")
        self.assertEqual(engine.evaluate("mymcp_search"), "allow")
        self.assertEqual(engine.evaluate("mymcp_write"), "ask")

    def test_catch_all_wildcard_applies_when_nothing_else_matches(self):
        cfg = OmniAgentConfig(permission=PermissionConfig(rules={"*": "ask"}))
        engine = PermissionEngine(cfg, mode="build")
        self.assertEqual(engine.evaluate("anything"), "ask")

    def test_unmatched_tool_defaults_to_allow(self):
        engine = PermissionEngine(OmniAgentConfig(), mode="build")
        self.assertEqual(engine.evaluate("read"), "allow")


class TestPermissionEngineCheck(unittest.TestCase):

    def setUp(self):
        self.test_bus = EventBus()
        self.patcher = patch.object(engine_module, "bus", self.test_bus)
        self.patcher.start()
        self.received = []
        self.test_bus.subscribe(WILDCARD, lambda e: self.received.append((e.type, getattr(e, "decision", None))))

    def tearDown(self):
        self.patcher.stop()

    def test_allow_returns_true_without_publishing_events(self):
        engine = PermissionEngine(OmniAgentConfig(), mode="build")
        self.assertTrue(engine.check("read", agent="coder"))
        self.assertEqual(self.received, [])

    def test_deny_returns_false_and_publishes_resolution(self):
        engine = PermissionEngine(OmniAgentConfig(), mode="plan")
        self.assertFalse(engine.check("bash", agent="executor"))
        self.assertIn(("permission.resolved", "deny"), self.received)

    def test_ask_denies_by_default_when_not_interactive(self):
        cfg = OmniAgentConfig(permission=PermissionConfig(rules={"bash": "ask"}))
        engine = PermissionEngine(cfg, mode="build", interactive=False)
        self.assertFalse(engine.check("bash", agent="executor"))

    def test_ask_prompts_when_interactive_and_tty(self):
        cfg = OmniAgentConfig(permission=PermissionConfig(rules={"bash": "ask"}))
        engine = PermissionEngine(
            cfg, mode="build", interactive=True,
            prompt=lambda tool, agent, reason: True,
        )
        with patch("sys.stdin.isatty", return_value=True):
            self.assertTrue(engine.check("bash", agent="executor"))
        self.assertIn(("permission.resolved", "allow"), self.received)

    def test_ask_with_prompt_declining_denies(self):
        cfg = OmniAgentConfig(permission=PermissionConfig(rules={"bash": "ask"}))
        engine = PermissionEngine(
            cfg, mode="build", interactive=True,
            prompt=lambda tool, agent, reason: False,
        )
        with patch("sys.stdin.isatty", return_value=True):
            self.assertFalse(engine.check("bash", agent="executor"))

    def test_auto_mode_approves_ask_rules(self):
        cfg = OmniAgentConfig(permission=PermissionConfig(rules={"bash": "ask"}, auto=True))
        engine = PermissionEngine(cfg, mode="build", interactive=False)
        self.assertTrue(engine.check("bash", agent="executor"))
        self.assertIn(("permission.resolved", "allow"), self.received)

    def test_auto_mode_does_not_override_explicit_deny(self):
        cfg = OmniAgentConfig(permission=PermissionConfig(rules={"bash": "deny"}, auto=True))
        engine = PermissionEngine(cfg, mode="build", interactive=False)
        self.assertFalse(engine.check("bash", agent="executor"))


class TestPermissionEngineResolver(unittest.TestCase):
    """The seam server/permission_bridge.py plugs into."""

    def setUp(self):
        self.test_bus = EventBus()
        self.patcher = patch.object(engine_module, "bus", self.test_bus)
        self.patcher.start()
        self.received = []
        self.test_bus.subscribe(WILDCARD, lambda e: self.received.append(e))

    def tearDown(self):
        self.patcher.stop()

    def test_resolver_is_used_for_ask_rules_even_without_interactive_tty(self):
        cfg = OmniAgentConfig(permission=PermissionConfig(rules={"bash": "ask"}))
        resolver_calls = []

        def fake_resolver(tool, agent, reason, request_id):
            resolver_calls.append((tool, agent, reason, request_id))
            return True

        # interactive=False and no tty — a plain terminal prompt would deny
        # by default, but a resolver should still be consulted.
        engine = PermissionEngine(cfg, mode="build", interactive=False, resolver=fake_resolver)

        self.assertTrue(engine.check("bash", agent="executor", reason="run tests"))
        self.assertEqual(len(resolver_calls), 1)
        self.assertEqual(resolver_calls[0][:3], ("bash", "executor", "run tests"))

    def test_resolver_takes_priority_over_terminal_prompt(self):
        cfg = OmniAgentConfig(permission=PermissionConfig(rules={"bash": "ask"}))
        prompt_calls = []

        engine = PermissionEngine(
            cfg, mode="build", interactive=True,
            prompt=lambda tool, agent, reason: prompt_calls.append(1) or True,
            resolver=lambda tool, agent, reason, request_id: False,
        )

        with patch("sys.stdin.isatty", return_value=True):
            result = engine.check("bash", agent="executor")

        self.assertFalse(result)  # resolver's answer, not the prompt's
        self.assertEqual(prompt_calls, [])  # prompt never called

    def test_requested_and_resolved_events_share_the_same_request_id(self):
        cfg = OmniAgentConfig(permission=PermissionConfig(rules={"bash": "ask"}))
        engine = PermissionEngine(
            cfg, mode="build",
            resolver=lambda tool, agent, reason, request_id: True,
        )

        engine.check("bash", agent="executor")

        requested = next(e for e in self.received if e.type == "permission.requested")
        resolved = next(e for e in self.received if e.type == "permission.resolved")

        self.assertIsNotNone(requested.request_id)
        self.assertEqual(requested.request_id, resolved.request_id)

    def test_auto_mode_still_generates_a_request_id(self):
        cfg = OmniAgentConfig(permission=PermissionConfig(rules={"bash": "ask"}, auto=True))
        engine = PermissionEngine(cfg, mode="build")

        engine.check("bash", agent="executor")

        requested = next(e for e in self.received if e.type == "permission.requested")
        resolved = next(e for e in self.received if e.type == "permission.resolved")
        self.assertEqual(requested.request_id, resolved.request_id)
        self.assertIsNotNone(requested.request_id)


class TestPermissionDenied(unittest.TestCase):

    def test_error_message_includes_tool_and_reason(self):
        err = PermissionDenied("bash", reason="plan mode")
        self.assertIn("bash", str(err))
        self.assertIn("plan mode", str(err))


if __name__ == "__main__":
    unittest.main()
