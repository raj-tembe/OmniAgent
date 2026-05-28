import ast
from typing import Dict


# syntax checker tool

class SyntaxCheckerTool:
    """
    Python syntax validation tool.

    Responsibilities:
    - validate Python syntax
    - detect parsing failures
    - support autonomous debugging
    """


    # check python syntax

    @staticmethod
    def check_syntax(
        code: str
    ) -> Dict:
        """
        Validate Python syntax.
        """

        try:

            ast.parse(code)

            return {

                "success": True,

                "valid": True,

                "error": None
            }

        except SyntaxError as e:

            return {

                "success": False,

                "valid": False,

                "error": {

                    "message": str(e),

                    "line": e.lineno,

                    "offset": e.offset,

                    "text": e.text
                }
            }

        except Exception as e:

            return {

                "success": False,

                "valid": False,

                "error": str(e)
            }


# global helper 

syntax_checker = SyntaxCheckerTool()