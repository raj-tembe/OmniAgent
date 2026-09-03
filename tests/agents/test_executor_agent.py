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
            next_agent="critic",
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
            next_agent="coder",
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

    def test_web_validation_success_routes_to_critic(self):
        execution_result = ExecutionResult(
            execution_status="success",
            execution_success=True,
            stdout="Web application validation passed",
            stderr="",
            error_message=None,
            executed_command="python _validate.py",
            generated_output_files=[],
            execution_time=0.2,
            next_agent="critic",
        )

        with patch(
            "agents.executor.executor_agent.execute_generated_project",
            return_value=execution_result,
        ):
            result = executor_agent({
                "generated_files": {"app.py": "from flask import Flask\napp = Flask(__name__)"},
                "retry_count": 0,
            })

        self.assertTrue(result["execution_success"])
        self.assertEqual(result["next_agent"], "critic")
        self.assertEqual(result["retry_count"], 0)

    def test_plan_mode_blocks_execution_without_calling_sandbox(self):
        with patch("agents.executor.executor_agent.execute_generated_project") as mock_execute:
            result = executor_agent({
                "generated_files": {"app.py": "print(1)"},
                "retry_count": 0,
                "agent_mode": "plan",
            })

        mock_execute.assert_not_called()
        self.assertFalse(result["execution_success"])
        self.assertEqual(result["next_agent"], "end")
        self.assertIn("plan", result["error_message"])
        self.assertIn("not permitted", result["messages"][0].content)

    def test_plan_mode_with_auto_approve_still_denies_explicit_deny(self):
        # auto_approve only auto-resolves "ask" rules; plan mode's builtin
        # defaults are "deny", which auto-approve must never override.
        with patch("agents.executor.executor_agent.execute_generated_project") as mock_execute:
            result = executor_agent({
                "generated_files": {"app.py": "print(1)"},
                "retry_count": 0,
                "agent_mode": "plan",
                "auto_approve": True,
            })

        mock_execute.assert_not_called()
        self.assertFalse(result["execution_success"])

    def test_build_mode_permits_execution_by_default(self):
        execution_result = ExecutionResult(
            execution_status="success",
            execution_success=True,
            stdout="OK",
            stderr="",
            error_message=None,
            executed_command="python app.py",
            generated_output_files=[],
            execution_time=0.1,
            next_agent="critic",
        )

        with patch(
            "agents.executor.executor_agent.execute_generated_project",
            return_value=execution_result,
        ) as mock_execute:
            result = executor_agent({
                "generated_files": {"app.py": "print(1)"},
                "retry_count": 0,
                "agent_mode": "build",
            })

        mock_execute.assert_called_once()
        self.assertTrue(result["execution_success"])

    def test_successful_execution_marks_matching_todo_completed(self):
        execution_result = ExecutionResult(
            execution_status="success",
            execution_success=True,
            stdout="OK",
            stderr="",
            error_message=None,
            executed_command="python app.py",
            generated_output_files=[],
            execution_time=0.1,
            next_agent="critic",
        )
        todos = [
            {"id": "abc123", "content": "Build UI", "status": "in_progress"},
            {"id": "def456", "content": "Add save button", "status": "pending"},
        ]

        with patch(
            "agents.executor.executor_agent.execute_generated_project",
            return_value=execution_result,
        ):
            result = executor_agent({
                "generated_files": {"app.py": "print(1)"},
                "retry_count": 0,
                "current_step": "Build UI",
                "todos": todos,
            })

        updated = next(t for t in result["todos"] if t["content"] == "Build UI")
        self.assertEqual(updated["status"], "completed")
        untouched = next(t for t in result["todos"] if t["content"] == "Add save button")
        self.assertEqual(untouched["status"], "pending")

    def test_failed_execution_does_not_mark_todo_completed(self):
        execution_result = ExecutionResult(
            execution_status="failed",
            execution_success=False,
            stdout="",
            stderr="Error",
            error_message="Runtime failure",
            executed_command="python app.py",
            generated_output_files=[],
            execution_time=0.1,
            next_agent="coder",
        )
        todos = [{"id": "abc123", "content": "Build UI", "status": "in_progress"}]

        with patch(
            "agents.executor.executor_agent.execute_generated_project",
            return_value=execution_result,
        ):
            result = executor_agent({
                "generated_files": {"app.py": "print(1)"},
                "retry_count": 0,
                "current_step": "Build UI",
                "todos": todos,
            })

        updated = next(t for t in result["todos"] if t["content"] == "Build UI")
        self.assertEqual(updated["status"], "in_progress")

    def test_server_mode_ask_rule_resolves_via_server_resolver_not_terminal(self):
        """
        With agent_mode="plan" the builtin default for "write"/"bash" is
        "deny" outright — to exercise the resolver path specifically, use a
        config that turns "write"/"bash" into "ask" instead, then prove
        server_mode routes through server.permission_bridge rather than
        falling back to a denied-by-default non-interactive prompt.
        """
        execution_result = ExecutionResult(
            execution_status="success",
            execution_success=True,
            stdout="OK",
            stderr="",
            error_message=None,
            executed_command="python app.py",
            generated_output_files=[],
            execution_time=0.1,
            next_agent="critic",
        )

        from config.schema import OmniAgentConfig, PermissionConfig
        ask_config = OmniAgentConfig(permission=PermissionConfig(rules={"write": "ask", "bash": "ask"}))

        with patch("agents.executor.executor_agent.load_config", return_value=ask_config), \
             patch("server.permission_bridge.make_server_resolver", return_value=lambda *a: True) as mock_make_resolver, \
             patch(
                 "agents.executor.executor_agent.execute_generated_project",
                 return_value=execution_result,
             ) as mock_execute:
            result = executor_agent({
                "generated_files": {"app.py": "print(1)"},
                "retry_count": 0,
                "agent_mode": "build",
                "server_mode": True,
            })

        mock_make_resolver.assert_called_once()
        mock_execute.assert_called_once()
        self.assertTrue(result["execution_success"])

    def test_non_server_mode_does_not_construct_a_resolver(self):
        execution_result = ExecutionResult(
            execution_status="success",
            execution_success=True,
            stdout="OK",
            stderr="",
            error_message=None,
            executed_command="python app.py",
            generated_output_files=[],
            execution_time=0.1,
            next_agent="critic",
        )

        with patch("server.permission_bridge.make_server_resolver") as mock_make_resolver, \
             patch(
                 "agents.executor.executor_agent.execute_generated_project",
                 return_value=execution_result,
             ):
            executor_agent({
                "generated_files": {"app.py": "print(1)"},
                "retry_count": 0,
                "agent_mode": "build",
                "server_mode": False,
            })

        mock_make_resolver.assert_not_called()
