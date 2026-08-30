import unittest

from pydantic import ValidationError

from config.schema import (
    AgentModeConfig,
    McpServerConfig,
    OmniAgentConfig,
    PermissionConfig,
)


class TestOmniAgentConfigSchema(unittest.TestCase):

    def test_defaults_are_empty_but_valid(self):
        cfg = OmniAgentConfig()

        self.assertEqual(cfg.permission.rules, {})
        self.assertFalse(cfg.permission.auto)
        self.assertEqual(cfg.agent, {})
        self.assertEqual(cfg.provider, {})
        self.assertEqual(cfg.mcp, {})
        self.assertEqual(cfg.plugin, [])

    def test_schema_alias_accepts_dollar_schema_key(self):
        cfg = OmniAgentConfig.model_validate({"$schema": "https://omniagent.dev/config.json"})
        self.assertEqual(cfg.schema_, "https://omniagent.dev/config.json")

    def test_invalid_permission_action_is_rejected(self):
        with self.assertRaises(ValidationError):
            PermissionConfig(rules={"bash": "maybe"})

    def test_wildcard_permission_rule_is_accepted(self):
        cfg = PermissionConfig(rules={"mymcp_*": "ask", "bash": "deny"})
        self.assertEqual(cfg.rules["mymcp_*"], "ask")
        self.assertEqual(cfg.rules["bash"], "deny")

    def test_agent_mode_requires_valid_mode(self):
        with self.assertRaises(ValidationError):
            AgentModeConfig(mode="autopilot")

        cfg = AgentModeConfig(mode="plan")
        self.assertEqual(cfg.mode, "plan")
        self.assertIsNone(cfg.permission)

    def test_mcp_server_config_local_vs_remote(self):
        local = McpServerConfig(type="local", command=["npx", "some-mcp-server"])
        remote = McpServerConfig(type="remote", url="https://example.com/mcp")

        self.assertEqual(local.type, "local")
        self.assertEqual(remote.url, "https://example.com/mcp")

    def test_full_config_round_trips_through_dict(self):
        raw = {
            "permission": {"rules": {"bash": "ask", "edit": "allow"}, "auto": True},
            "agent": {"plan": {"mode": "plan"}},
            "provider": {"gemini": {"model": "gemini-2.5-flash"}},
            "mcp": {"github": {"type": "remote", "url": "https://mcp.github.com"}},
            "plugin": ["omniagent-example-plugin"],
        }

        cfg = OmniAgentConfig.model_validate(raw)

        self.assertEqual(cfg.permission.rules["bash"], "ask")
        self.assertTrue(cfg.permission.auto)
        self.assertEqual(cfg.agent["plan"].mode, "plan")
        self.assertEqual(cfg.provider["gemini"].model, "gemini-2.5-flash")
        self.assertEqual(cfg.mcp["github"].url, "https://mcp.github.com")
        self.assertEqual(cfg.plugin, ["omniagent-example-plugin"])


if __name__ == "__main__":
    unittest.main()
