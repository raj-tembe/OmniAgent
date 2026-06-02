import subprocess
from typing import Dict, Optional


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

                "-v",
                f"{working_directory}:/app",

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
        command: str,
        working_directory: str,
        timeout: int = 60
    ) -> Dict:
        """
        Execute shell command in Docker.
        """

        try:

            docker_command = [

                "docker",
                "run",

                "--rm",

                "-v",
                f"{working_directory}:/app",

                "-w",
                "/app",

                "python:3.11-slim",

                "sh",
                "-c",
                command
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