import contextlib
import io
import traceback
from typing import Dict


# python repl tool

class PythonREPLTool:
    """
    Dynamic Python execution tool.

    Responsibilities:
    - execute Python snippets
    - capture stdout/stderr
    - support debugging workflows
    - provide runtime experimentation
    """

    def __init__(self):
        pass


    # execute tool

    def execute(
        self,
        code: str
    ) -> Dict:
        """
        Execute Python code safely with fresh globals for each execution.
        """

        fresh_globals = {}
        stdout_buffer = io.StringIO()

        try:

            with contextlib.redirect_stdout(
                stdout_buffer
            ):

                exec(code, fresh_globals)

            return {

                "success": True,

                "stdout": (
                    stdout_buffer.getvalue()
                ),

                "error": None
            }

        except Exception:

            return {

                "success": False,

                "stdout": (
                    stdout_buffer.getvalue()
                ),

                "error": traceback.format_exc()
            }


# global helper 

python_repl = PythonREPLTool()