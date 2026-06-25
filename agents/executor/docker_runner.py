import subprocess
import time
import shlex
import os
from pathlib import Path
from typing import List, Union
from schemas.execution_schema import ExecutionResult


Command = Union[str, List[str]]


def _normalize_command(command: Command) -> List[str]:
    if isinstance(command, str):
        return shlex.split(command)
    return command


def run_in_docker(
        project_path: str,
        command: Command = "python app.py",
        timeout: int = 60,
) -> ExecutionResult:
    """
    executes generated prject in side docker container."""

    start_time = time.time()
    resolved_project_path = str(Path(project_path).resolve())
    command_args = _normalize_command(command)
    docker_command = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "--memory",
        "256m",
        "--cpus",
        "1",
        "--pids-limit",
        "128",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "-v",
        f"{resolved_project_path}:/app:rw",
        "-w",
        "/app",
        "python:3.11",
        *command_args
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

            executed_command=" ".join(command_args),

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
            executed_command=" ".join(command_args),
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
            executed_command=" ".join(command_args),
            execution_time=time.time() - start_time,
            next_agent="human"
        )
