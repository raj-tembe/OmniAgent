import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from config.schema import McpServerConfig
from mcp_client.client import McpError, _with_session, call_tool, list_tools


class TestWithSessionValidation(unittest.TestCase):
    """These don't need the SDK mocked — they fail before touching it."""

    def test_local_without_command_raises(self):
        server = McpServerConfig(type="local")
        with self.assertRaises(McpError):
            asyncio.run(_with_session(server, lambda session: None))

    def test_remote_without_url_raises(self):
        server = McpServerConfig(type="remote")
        with self.assertRaises(McpError):
            asyncio.run(_with_session(server, lambda session: None))


class TestListTools(unittest.TestCase):

    def test_returns_tools_from_async_implementation(self):
        server = McpServerConfig(type="local", command=["npx", "some-server"])
        fake_tools = [{"name": "search", "description": "Search things.", "input_schema": {}}]

        with patch("mcp_client.client._list_tools_async", new=AsyncMock(return_value=fake_tools)):
            result = list_tools(server)

        self.assertEqual(result, fake_tools)

    def test_wraps_unexpected_exception_as_mcp_error(self):
        server = McpServerConfig(type="local", command=["npx", "some-server"])

        async def boom(_server):
            raise RuntimeError("connection refused")

        with patch("mcp_client.client._list_tools_async", new=boom):
            with self.assertRaises(McpError) as ctx:
                list_tools(server)

        self.assertIn("connection refused", str(ctx.exception))

    def test_timeout_raises_mcp_error(self):
        server = McpServerConfig(type="local", command=["npx", "some-server"])

        async def hang(_server):
            await asyncio.sleep(10)

        with patch("mcp_client.client._list_tools_async", new=hang):
            with self.assertRaises(McpError) as ctx:
                list_tools(server, timeout=0.01)

        self.assertIn("Timed out", str(ctx.exception))


class TestCallTool(unittest.TestCase):

    def test_returns_result_from_async_implementation(self):
        server = McpServerConfig(type="remote", url="https://example.com/mcp")
        fake_result = {"success": True, "content": "42"}

        with patch("mcp_client.client._call_tool_async", new=AsyncMock(return_value=fake_result)):
            result = call_tool(server, "calculate", {"expression": "6*7"})

        self.assertEqual(result, fake_result)

    def test_wraps_unexpected_exception_as_mcp_error(self):
        server = McpServerConfig(type="remote", url="https://example.com/mcp")

        async def boom(_server, _tool, _args):
            raise RuntimeError("server crashed")

        with patch("mcp_client.client._call_tool_async", new=boom):
            with self.assertRaises(McpError) as ctx:
                call_tool(server, "calculate", {})

        self.assertIn("server crashed", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
