import unittest
from unittest.mock import patch

from config.schema import McpServerConfig, OmniAgentConfig, PermissionConfig
from mcp_client.client import McpError
from mcp_client.registry import call_server_tool, discover_all_tools, enabled_servers
from permission import PermissionEngine


def _config(**servers) -> OmniAgentConfig:
    return OmniAgentConfig(mcp=servers)


class TestEnabledServers(unittest.TestCase):

    def test_filters_out_disabled_servers(self):
        config = _config(
            a=McpServerConfig(type="remote", url="https://a.example.com", enabled=True),
            b=McpServerConfig(type="remote", url="https://b.example.com", enabled=False),
        )

        result = enabled_servers(config)

        self.assertEqual(list(result.keys()), ["a"])


class TestDiscoverAllTools(unittest.TestCase):

    def test_aggregates_tools_across_servers(self):
        config = _config(
            a=McpServerConfig(type="remote", url="https://a.example.com"),
            b=McpServerConfig(type="remote", url="https://b.example.com"),
        )

        def fake_list_tools(server, timeout=30.0):
            return [{"name": "tool_for_" + server.url[8:9]}]

        with patch("mcp_client.registry.list_tools", side_effect=fake_list_tools):
            result = discover_all_tools(config)

        self.assertEqual(set(result.keys()), {"a", "b"})
        self.assertEqual(len(result["a"]), 1)

    def test_one_broken_server_does_not_block_the_others(self):
        config = _config(
            broken=McpServerConfig(type="remote", url="https://broken.example.com"),
            healthy=McpServerConfig(type="remote", url="https://healthy.example.com"),
        )

        def fake_list_tools(server, timeout=30.0):
            if "broken" in server.url:
                raise McpError("connection refused")
            return [{"name": "search"}]

        with patch("mcp_client.registry.list_tools", side_effect=fake_list_tools):
            result = discover_all_tools(config)

        self.assertEqual(result["broken"], [])
        self.assertEqual(len(result["healthy"]), 1)


class TestCallServerTool(unittest.TestCase):

    def test_unconfigured_server_returns_error_without_calling_client(self):
        config = _config()

        with patch("mcp_client.registry.call_tool") as mock_call:
            result = call_server_tool(config, "nonexistent", "search", {})

        mock_call.assert_not_called()
        self.assertFalse(result["success"])
        self.assertIn("not configured", result["error"])

    def test_successful_call_without_permission_engine(self):
        config = _config(github=McpServerConfig(type="remote", url="https://mcp.github.com"))

        with patch("mcp_client.registry.call_tool", return_value={"success": True, "content": "ok"}):
            result = call_server_tool(config, "github", "search_issues", {"q": "bug"})

        self.assertTrue(result["success"])

    def test_permission_engine_denies_call(self):
        config = _config(github=McpServerConfig(type="remote", url="https://mcp.github.com"))

        cfg_with_deny = OmniAgentConfig(
            mcp=config.mcp,
            permission=PermissionConfig(rules={"github_search_issues": "deny"}),
        )
        engine = PermissionEngine(cfg_with_deny, mode="build")

        with patch("mcp_client.registry.call_tool") as mock_call:
            result = call_server_tool(cfg_with_deny, "github", "search_issues", {}, permission_engine=engine)

        mock_call.assert_not_called()
        self.assertFalse(result["success"])
        self.assertIn("Permission denied", result["error"])

    def test_permission_engine_wildcard_allows_call(self):
        config = OmniAgentConfig(
            mcp={"github": McpServerConfig(type="remote", url="https://mcp.github.com")},
            permission=PermissionConfig(rules={"github_*": "allow"}),
        )
        engine = PermissionEngine(config, mode="plan")  # plan mode would otherwise deny writes

        with patch("mcp_client.registry.call_tool", return_value={"success": True, "content": "ok"}) as mock_call:
            result = call_server_tool(config, "github", "search_issues", {}, permission_engine=engine)

        mock_call.assert_called_once()
        self.assertTrue(result["success"])

    def test_mcp_error_from_client_is_returned_as_error_dict(self):
        config = _config(github=McpServerConfig(type="remote", url="https://mcp.github.com"))

        with patch("mcp_client.registry.call_tool", side_effect=McpError("timed out")):
            result = call_server_tool(config, "github", "search_issues", {})

        self.assertFalse(result["success"])
        self.assertIn("timed out", result["error"])


if __name__ == "__main__":
    unittest.main()
