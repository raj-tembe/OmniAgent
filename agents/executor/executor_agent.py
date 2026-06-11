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

    if execution_result.execution_success:
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

    # Return updated state
    return {
        "messages": [
            AIMessage(
                content=executor_message
            )
        ],

        #execution results
        "execution_success": execution_result.execution_success,
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
        "retry_count": retry_count + (0 if execution_result.execution_success else 1)
    }