import subprocess
import shlex
import os
from pathlib import Path
from typing import Dict, List, Optional, Union


# docker executer 

class DockerExecutor:
    """
    Docker-based isolated code execution.

    Responsibilities:
    - execute code safely
    - isolate runtime environment
    - prevent host contamination
    - support autonomous execution
    """


    # run python file 

    @staticmethod
    def run_python_file(
        file_path: str,
        working_directory: str,
        timeout: int = 60
    ) -> Dict:
        """
        Execute Python file inside Docker.
        """

        try:

            command = [

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
                f"{Path(working_directory).resolve()}:/app:rw",

                "-w",
                "/app",

                "python:3.11-slim",

                "python",
                file_path
            ]

            result = subprocess.run(

                command,

                capture_output=True,

                text=True,

                timeout=timeout
            )

            success = (
                result.returncode == 0
            )

            return {

                "success": success,

                "stdout": result.stdout,

                "stderr": result.stderr,

                "return_code": (
                    result.returncode
                )
            }

        except subprocess.TimeoutExpired:

            return {

                "success": False,

                "stdout": "",

                "stderr": (
                    "Execution timed out."
                )
            }

        except Exception as e:

            return {

                "success": False,

                "stdout": "",

                "stderr": str(e)
            }


    # run shell command 

    @staticmethod
    def run_command(
        command: Union[str, List[str]],
        working_directory: str,
        timeout: int = 60
    ) -> Dict:
        """
        Execute shell command in Docker.
        """

        try:
            command_args = shlex.split(command) if isinstance(command, str) else command

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
                f"{Path(working_directory).resolve()}:/app:rw",

                "-w",
                "/app",

                "python:3.11-slim",

                *command_args
            ]

            result = subprocess.run(

                docker_command,

                capture_output=True,

                text=True,

                timeout=timeout
            )

            return {

                "success": (
                    result.returncode == 0
                ),

                "stdout": result.stdout,

                "stderr": result.stderr,

                "return_code": (
                    result.returncode
                )
            }

        except Exception as e:

            return {

                "success": False,

                "stdout": "",

                "stderr": str(e)
            }


# global executer 

docker_executor = DockerExecutor()
