import subprocess
import time
from typing import Dict
from schemas.execution_schema import ExecutionResult

def run_in_docker(
        project_path: str,
        command: str = "python app.py",
        timeout: int = 60,
) -> ExecutionResult:
    """
    executes generated prject in side docker container."""

    start_time = time.time()
    docker_command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{project_path}:/app",
        "-w",
        "/app",
        "python:3.11",
        "sh",
        "-c",
        command
    ]
    
    try:
        result = subprocess.run(
            docker_command,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        execution_time = time.time() - start_time
        success = result.returncode == 0

        return ExecutionResult(
            execution_status=(
                "success" if success else "failed"
                ),

            execution_success=success,

            stdout=result.stdout,

            stderr=result.stderr,

            error_message=(
                result.stderr if not success else None
                ),

            executed_command=command,

            execution_time=execution_time,

            next_agent=(
                "critic" if success else "coder"
                )
        )
    
    except subprocess.TimeoutExpired:
        return ExecutionResult(
            execution_status="timeout",
            execution_success=False,
            stdout="",
            stderr="Execution timed out.",
            error_message="Execution exceeded the timeout limit.",
            executed_command=command,
            execution_time=timeout,
            next_agent="coder"
        )
    
    except Exception as e:
        
        return ExecutionResult(
            execution_status="crashed",
            execution_success=False,
            stdout="",
            stderr=str(e),
            error_message=str(e),
            executed_command=command,
            execution_time=time.time() - start_time,
            next_agent="human"
        )