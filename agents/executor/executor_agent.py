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

            "retry_count": retry_count + 1

        }

    # Execute generated project
    execution_result = execute_generated_project(
        generated_files=generated_files
    )

    # Execution success 
    if execution_result.execution_success:
        
        executer_message = (
            "Executer Agent: "
            "Project executed successfully.\n\n"
            f"Execution time: "
            f"{execution_result.execution_time:.2f} seconds."
        )

    # Return upadted state
    return {

        "messages": [
            AIMessage(
                content=executer_message
            )
        ],
        #execution results
        "execution_success":( 
            execution_result.execution_success
            ),

        "execution_status": (
            execution_result.execution_status
            ),

        "execution_output": (
            execution_result.stdout
            ),

        "execution_logs": (
            f"STDOUT:\n{execution_result.stdout}\n\n"
            f"STDERR:\n{execution_result.stderr}"
            ),

        "error_message": (
            execution_result.error_message
            ),

        "execution_time": (
            execution_result.execution_time
            ),

        #workflow
        "next_agent": (
            execution_result.next_agent
            ),

        #retry tracking
        "retry_count": (
            retry_count + (
            0 if execution_result.execution_success 
            else 1  
            )
        )
    }