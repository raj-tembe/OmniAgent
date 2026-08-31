import unittest
from unittest.mock import MagicMock, patch

from agents.critic.critic_agent import critic_agent
from schemas.critic_schema import CriticOutput


def _fake_response(**overrides):
    defaults = dict(
        review_status="approved",
        quality_score=9.0,
        summary="Looks good.",
        feedback="No changes needed.",
        issues=[],
        security_issues=[],
        architecture_review=None,
        testing_review=None,
        improvement_suggestions=[],
        next_agent="end",
        requires_human_approval=False,
    )
    defaults.update(overrides)
    return CriticOutput(**defaults)


class TestCriticAgentLspWiring(unittest.TestCase):

    def test_diagnostics_from_real_pylsp_are_passed_to_the_chain(self):
        """
        End-to-end through the real lsp/ package (no mocking of get_diagnostics
        itself) — proves the wiring reaches an actual language server and the
        result lands in the critic chain's invoke payload.
        """
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = _fake_response()

        with patch("agents.critic.critic_agent.create_critic_chain", return_value=mock_chain):
            critic_agent({
                "generated_files": {"app.py": "def foo():\n    return undefined_name_here\n"},
                "current_step": "Build app",
            })

        payload = mock_chain.invoke.call_args[0][0]
        self.assertIn("undefined_name_here", payload["lsp_diagnostics"])
        self.assertIn("app.py", payload["lsp_diagnostics"])

    def test_unsupported_extensions_are_skipped_without_error(self):
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = _fake_response()

        with patch("agents.critic.critic_agent.create_critic_chain", return_value=mock_chain):
            critic_agent({
                "generated_files": {"notes.rb": "puts 'hi'"},
                "current_step": "Build app",
            })

        payload = mock_chain.invoke.call_args[0][0]
        self.assertIn("no diagnostics", payload["lsp_diagnostics"])

    def test_lsp_error_for_one_file_does_not_block_review(self):
        from lsp.client import LspError

        mock_chain = MagicMock()
        mock_chain.invoke.return_value = _fake_response()

        with patch("agents.critic.critic_agent.create_critic_chain", return_value=mock_chain), \
             patch("agents.critic.critic_agent.get_diagnostics", side_effect=LspError("timed out")):
            result = critic_agent({
                "generated_files": {"app.py": "x = 1\n"},
                "current_step": "Build app",
            })

        # should complete normally, not raise
        self.assertEqual(result["review_status"], "approved")

    def test_clean_file_produces_placeholder_text(self):
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = _fake_response()

        with patch("agents.critic.critic_agent.create_critic_chain", return_value=mock_chain):
            critic_agent({
                "generated_files": {"clean.py": '"""Clean module."""\n\n\ndef add(a: int, b: int) -> int:\n    return a + b\n'},
                "current_step": "Build app",
            })

        payload = mock_chain.invoke.call_args[0][0]
        self.assertIn("no diagnostics", payload["lsp_diagnostics"])


if __name__ == "__main__":
    unittest.main()
