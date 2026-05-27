import subprocess
from typing import Dict, Optional


# terminal runner tool

class TerminalRunnerTool:
    """
    Terminal command execution tool.

    Responsibilities:
    - execute shell commands
    - capture stdout/stderr
    - support workflow automation
    - assist execution/debugging
    """


    # run command

    @staticmethod
    def run_command(
        command: str,
        cwd: Optional[str] = None,
        timeout: int = 60
    ) -> Dict:
        """
        Execute terminal command.
        """

        try:

            result = subprocess.run(

                command,

                shell=True,

                capture_output=True,

                text=True,

                cwd=cwd,

                timeout=timeout
            )

            success = (
                result.returncode == 0
            )

            return {

                "success": success,

                "command": command,

                "stdout": result.stdout,

                "stderr": result.stderr,

                "return_code": (
                    result.returncode
                )
            }

        except subprocess.TimeoutExpired:

            return {

                "success": False,

                "command": command,

                "stdout": "",

                "stderr": (
                    "Command timed out."
                )
            }

        except Exception as e:

            return {

                "success": False,

                "command": command,

                "stdout": "",

                "stderr": str(e)
            }


# global helper 

terminal_runner = TerminalRunnerTool()