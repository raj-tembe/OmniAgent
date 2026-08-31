import unittest
from unittest.mock import patch

from agents.planner.planner_agent import planner_agent
from schemas.planner_schema import PlannerOutput


class TestPlannerRouting(unittest.TestCase):
    def test_researcher_routing_is_preserved(self):
        response = PlannerOutput(
            tasks=["Research the request"],
            current_step="Research the request",
            workflow_status="researching",
            next_agent="researcher",
            reasoning="Need more context",
            recovery_strategy=None,
            require_human_approval=False,
        )

        with patch("agents.planner.planner_agent.create_planner_chain") as mock_chain:
            mock_chain.return_value.invoke.return_value = response
            result = planner_agent({"messages": [], "user_request": "Build a CLI"})

        self.assertEqual(result["next_agent"], "researcher")
        self.assertEqual(result["workflow_status"], "researching")

    def test_repeated_failure_escalates_to_critic_with_subagent_diagnosis(self):
        response = PlannerOutput(
            tasks=["Fix the bug"],
            current_step="Fix the bug",
            workflow_status="failed",
            next_agent="coder",
            reasoning="Still broken",
            recovery_strategy=None,
            require_human_approval=False,
        )

        with patch("agents.planner.planner_agent.create_planner_chain") as mock_chain, \
             patch("agents.planner.planner_agent.run_subagent", return_value="Likely a null pointer.") as mock_subagent:
            mock_chain.return_value.invoke.return_value = response
            result = planner_agent({
                "messages": [],
                "user_request": "Build a CLI",
                "retry_count": 3,
                "error_message": "NoneType has no attribute x",
            })

        mock_subagent.assert_called_once()
        self.assertEqual(result["next_agent"], "critic")
        self.assertIn("Likely a null pointer.", result["messages"][-1].content)

    def test_long_message_history_is_compacted_before_planning(self):
        from langchain_core.messages import HumanMessage

        response = PlannerOutput(
            tasks=["Do a thing"],
            current_step="Do a thing",
            workflow_status="planning",
            next_agent="coder",
            reasoning="ok",
            recovery_strategy=None,
            require_human_approval=False,
        )
        long_history = [HumanMessage(content="x" * 400) for _ in range(200)]

        with patch("agents.planner.planner_agent.create_planner_chain") as mock_chain, \
             patch("agents.planner.planner_agent.compact_messages") as mock_compact:
            mock_chain.return_value.invoke.return_value = response
            mock_compact.return_value = [HumanMessage(content="[summary]")]

            result = planner_agent({
                "messages": long_history,
                "user_request": "Build a CLI",
            })

        mock_compact.assert_called_once()
        # the returned messages list should be built on the compacted list,
        # not the original 200-message history
        self.assertEqual(len(result["messages"]), 2)  # summary + new planner message

    def test_short_message_history_is_not_compacted(self):
        from langchain_core.messages import HumanMessage

        response = PlannerOutput(
            tasks=["Do a thing"],
            current_step="Do a thing",
            workflow_status="planning",
            next_agent="coder",
            reasoning="ok",
            recovery_strategy=None,
            require_human_approval=False,
        )
        short_history = [HumanMessage(content="hi")]

        with patch("agents.planner.planner_agent.create_planner_chain") as mock_chain, \
             patch("agents.planner.planner_agent.compact_messages") as mock_compact:
            mock_chain.return_value.invoke.return_value = response

            planner_agent({"messages": short_history, "user_request": "Build a CLI"})

        mock_compact.assert_not_called()
