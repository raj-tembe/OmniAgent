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
