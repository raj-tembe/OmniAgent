import unittest
from unittest.mock import patch

from agents.executor.executor_agent import executor_agent
from schemas.execution_schema import ExecutionResult


class TestExecutorAgent(unittest.TestCase):

    def test_no_generated_files_routes_to_coder(self):
        state = {
            "generated_files": {},
            "retry_count": 1,
        }

        result = executor_agent(state)

        self.assertFalse(result["execution_success"])
        self.assertEqual(result["next_agent"], "coder")
        self.assertEqual(result["retry_count"], 2)
        self.assertIn("No generated files found", result["messages"][0].content)

    def test_execution_success_routes_to_critic(self):
        execution_result = ExecutionResult(
            execution_status="success",
            execution_success=True,
            stdout="OK",
            stderr="",
            error_message=None,
            executed_command="python app.py",
            generated_output_files=[],
            execution_time=0.5,
        )

        with patch(
            "agents.executor.executor_agent.execute_generated_project",
            return_value=execution_result,
        ):
            result = executor_agent({"generated_files": {"app.py": "print(1)"}, "retry_count": 0})

        self.assertTrue(result["execution_success"])
        self.assertEqual(result["next_agent"], "critic")
        self.assertEqual(result["retry_count"], 0)
        self.assertIn("Project executed successfully", result["messages"][0].content)

    def test_execution_failure_routes_to_coder_then_critic_after_retries(self):
        execution_result = ExecutionResult(
            execution_status="failed",
            execution_success=False,
            stdout="",
            stderr="Error",
            error_message="Runtime failure",
            executed_command="python app.py",
            generated_output_files=[],
            execution_time=0.1,
        )

        with patch(
            "agents.executor.executor_agent.execute_generated_project",
            return_value=execution_result,
        ):
            first = executor_agent({"generated_files": {"app.py": "print(1)"}, "retry_count": 0})
            second = executor_agent({"generated_files": {"app.py": "print(1)"}, "retry_count": 3})

        self.assertFalse(first["execution_success"])
        self.assertEqual(first["next_agent"], "coder")
        self.assertEqual(first["retry_count"], 1)

        self.assertFalse(second["execution_success"])
        self.assertEqual(second["next_agent"], "critic")
        self.assertEqual(second["retry_count"], 4)
