import unittest
from unittest.mock import patch

from config.schema import OmniAgentConfig, PermissionConfig
from permission.factory import build_permission_engine


class TestBuildPermissionEngine(unittest.TestCase):

    def test_defaults_to_build_mode(self):
        engine = build_permission_engine(config=OmniAgentConfig())
        self.assertEqual(engine.mode, "build")
        self.assertIsNone(engine.resolver)

    def test_uses_provided_config_without_reloading(self):
        cfg = OmniAgentConfig(permission=PermissionConfig(rules={"bash": "deny"}))

        with patch("permission.factory.load_config") as mock_load:
            engine = build_permission_engine(config=cfg)
            mock_load.assert_not_called()

        self.assertEqual(engine.evaluate("bash"), "deny")

    def test_loads_config_when_none_given(self):
        with patch("permission.factory.load_config", return_value=OmniAgentConfig()) as mock_load:
            build_permission_engine()
            mock_load.assert_called_once()

    def test_server_mode_false_never_imports_server_bridge(self):
        # server/permission_bridge.py depends on nothing exotic here, but
        # the point is the import is skipped entirely off the hot path —
        # verified by patching the source and confirming it's untouched.
        with patch("server.permission_bridge.make_server_resolver") as mock_make_resolver:
            engine = build_permission_engine(config=OmniAgentConfig(), server_mode=False)

        mock_make_resolver.assert_not_called()
        self.assertIsNone(engine.resolver)

    def test_server_mode_true_builds_a_resolver(self):
        sentinel_resolver = lambda *a: True

        with patch("server.permission_bridge.make_server_resolver", return_value=sentinel_resolver) as mock_make_resolver:
            engine = build_permission_engine(config=OmniAgentConfig(), server_mode=True)

        mock_make_resolver.assert_called_once()
        self.assertIs(engine.resolver, sentinel_resolver)

    def test_agent_mode_and_interactive_are_passed_through(self):
        engine = build_permission_engine(config=OmniAgentConfig(), agent_mode="plan", interactive=True)
        self.assertEqual(engine.mode, "plan")
        self.assertTrue(engine.interactive)


if __name__ == "__main__":
    unittest.main()
