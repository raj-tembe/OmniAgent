from typing import Dict
from langchain_core.messages import AIMessage
from graph.state import AgentState

from agents.executor.sandbox_runner import (
    execute_generated_project
)

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

    retry_count = state.get(
        "retry_count",
        0
    )

    current_step = state.get(
        "current_step",
        ""
    )

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

    # Execute generated project
    execution_result = execute_generated_project(
        generated_files=generated_files,
        project_name=project_name
    )

    # Detect if this is a web server app
    all_content = " ".join(generated_files.values())
    is_web_server = any(kw in all_content for kw in [
        "app.run(", "uvicorn", "Flask(", "FastAPI(", "django", "tornado"
    ])

    # For web servers that validate successfully, consider it a success
    # (validation passes = syntax OK + dependencies OK)
    execution_success = execution_result.execution_success
    if is_web_server and execution_result.execution_status == "completed":
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

        #workflow
        "next_agent": next_agent,
        "current_agent": "executor",
        "project_name": project_name,

        #retry tracking
        "retry_count": retry_count + retry_increment
    }