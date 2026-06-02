import subprocess
from typing import Dict, Optional


# isolated runner 

class IsolatedRunner:
    """
    Lightweight isolated execution runner.

    Responsibilities:
    - local isolated execution
    - rapid debugging workflows
    - development-time execution
    """

    def __init__(
        self,
        timeout: int = 30
    ):

        self.timeout = timeout


    # run python script

    def run_python_script(
        self,
        script_path: str,
        cwd: Optional[str] = None
    ) -> Dict:
        """
        Execute local Python script.
        """

        try:

            result = subprocess.run(

                ["python", script_path],

                capture_output=True,

                text=True,

                cwd=cwd,

                timeout=self.timeout
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


    # run terminal command 

    def run_command(
        self,
        command: str,
        cwd: Optional[str] = None
    ) -> Dict:
        """
        Execute shell command locally.
        """

        try:

            result = subprocess.run(

                command,

                shell=True,

                capture_output=True,

                text=True,

                cwd=cwd,

                timeout=self.timeout
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


# global runner 

isolated_runner = IsolatedRunner()