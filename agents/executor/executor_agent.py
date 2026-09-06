from typing import Dict
from langchain_core.messages import AIMessage
from graph.state import AgentState

from agents.executor.sandbox_runner import (
    execute_generated_project
)
from permission import build_permission_engine
from tools.agent_tools.todo_tool import TodoTool

def executor_agent(state: AgentState) -> Dict:
    """
    Execution Agent

    Responsibilities:
    - Save generated files.
    - Execute generated code
    - Capture runtime logs/errors
    - Detect failures
    - Route workflow intelligently
    """

    # Extract state
    generated_files = state.get(
        "generated_files",
        {}
    )

    project_name = state.get(
        "project_name",
        "current_project"
    )

    entry_point = state.get("entry_point", "app.py") or "app.py"

    retry_count = state.get(
        "retry_count",
        0
    )

    agent_mode = state.get("agent_mode", "build") or "build"
    interactive = state.get("interactive", False)
    session_id = state.get("session_id")
    server_mode = state.get("server_mode", False)

    #Validate generated files

    if not generated_files:
        return {
            "messages": [
                AIMessage(
                    content=(
                        "Execution Agent: "
                        "No generated files found."
                    )
                )
            ],  

            "execution_success": False,

            "error_message": (
                "No files available for execution."
                ),

            "next_agent": "coder",
            "current_agent": "executor",
            "project_name": project_name,

            "retry_count": retry_count + 1

        }

    # Permission check: writing generated files + running them in the
    # sandbox are exactly the "write"/"bash"-equivalent actions the
    # permission engine gates. Plan mode denies both by default; a custom
    # omniagent.json can loosen this to "ask" or "allow".
    permission_engine = build_permission_engine(agent_mode=agent_mode, interactive=interactive, server_mode=server_mode)
    if state.get("auto_approve"):
        permission_engine.auto = True

    if not permission_engine.check("write", agent="executor", reason="Save generated project files.", session_id=session_id):
        return {
            "messages": [
                AIMessage(content=(
                    "Execution Agent: "
                    f"Blocked — writing generated files is not permitted in '{agent_mode}' mode."
                ))
            ],
            "execution_success": False,
            "error_message": f"Permission denied: write (mode={agent_mode}).",
            "next_agent": "end",
            "current_agent": "executor",
            "project_name": project_name,
        }

    if not permission_engine.check("bash", agent="executor", reason="Run generated project in sandbox.", session_id=session_id):
        return {
            "messages": [
                AIMessage(content=(
                    "Execution Agent: "
                    f"Blocked — running generated code is not permitted in '{agent_mode}' mode."
                ))
            ],
            "execution_success": False,
            "error_message": f"Permission denied: bash (mode={agent_mode}).",
            "next_agent": "end",
            "current_agent": "executor",
            "project_name": project_name,
        }

    # Execute generated project
    execution_result = execute_generated_project(
        generated_files=generated_files,
        project_name=project_name,
        entry_point=entry_point,
    )

    # Detect if this is a web server app
    all_content = " ".join(generated_files.values())
    is_web_server = any(kw in all_content for kw in [
        "app.run(", "uvicorn", "Flask(", "FastAPI(", "django", "tornado"
    ])

    # For web servers that validate successfully, consider it a success
    # (validation passes = syntax OK + dependencies OK)
    execution_success = execution_result.execution_success
    if is_web_server and execution_result.execution_status == "success":
        execution_success = True

    if execution_success:
        if is_web_server:
            executor_message = (
                "Execution Agent: "
                "Web application structure validated successfully.\n\n"
                f"Execution time: {execution_result.execution_time:.2f} seconds."
            )
        else:
            executor_message = (
                "Execution Agent: "
                "Project executed successfully.\n\n"
                f"Execution time: {execution_result.execution_time:.2f} seconds."
            )
        next_agent = "critic"
    else:
        executor_message = (
            "Execution Agent: "
            "Project execution failed.\n\n"
            f"Error: {execution_result.error_message or 'Unknown error.'}"
        )
        next_agent = "coder" if retry_count < 3 else "critic"

    # Detect if failure was a web server timeout (not a real code error)
    is_timeout = execution_result.execution_status == "timeout"
    is_expected_timeout = is_web_server and is_timeout

    # Only increment retry_count for real failures, not expected web server timeouts
    retry_increment = 0 if is_expected_timeout else (
        0 if execution_success else 1
    )

    # Mark the current step's todo item completed once execution actually
    # succeeds — coder can only mark a step "in_progress" since it doesn't
    # know whether the step held up; this is where that's confirmed.
    todos = state.get("todos", [])
    current_step = state.get("current_step", "")
    if execution_success and current_step and todos:
        match = next((t for t in todos if t.get("content") == current_step), None)
        if match:
            todos = TodoTool.update_status(todos, match["id"], "completed")

    # Return updated state
    return {
        "messages": [
            AIMessage(
                content=executor_message
            )
        ],

        #execution results
        "execution_success": execution_success,
        "execution_status": execution_result.execution_status,
        "execution_output": execution_result.stdout,
        "execution_logs": (
            f"STDOUT:\n{execution_result.stdout}\n\n"
            f"STDERR:\n{execution_result.stderr}"
        ),
        "error_message": execution_result.error_message,
        "execution_time": execution_result.execution_time,

        #visible task list
        "todos": todos,

        #workflow
        "next_agent": next_agent,
        "current_agent": "executor",
        "project_name": project_name,

        #retry tracking
        "retry_count": retry_count + retry_increment
    }