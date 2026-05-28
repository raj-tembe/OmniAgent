import re
from typing import Dict, List


# security checker tool

class SecurityCheckerTool:
    """
    Security validation tool.

    Responsibilities:
    - detect dangerous code patterns
    - identify unsafe execution
    - support autonomous safety checks
    """


    # dangerous patterns

    DANGEROUS_PATTERNS = {

        "eval_usage": r"\beval\s*\(",

        "exec_usage": r"\bexec\s*\(",

        "os_system": r"\bos\.system\s*\(",

        "subprocess_shell_true": (
            r"shell\s*=\s*True"
        ),

        "pickle_usage": r"\bpickle\.load",

        "hardcoded_password": (
            r"password\s*=\s*[\"'].*[\"']"
        ),

        "hardcoded_api_key": (
            r"api_key\s*=\s*[\"'].*[\"']"
        ),

        "unsafe_yaml_load": (
            r"yaml\.load\s*\("
        )
    }


    # check security

    @classmethod
    def check_security(
        cls,
        code: str
    ) -> Dict:
        """
        Analyze code for security risks.
        """

        issues = []

        for issue_name, pattern in (
            cls.DANGEROUS_PATTERNS.items()
        ):

            matches = re.findall(
                pattern,
                code
            )

            if matches:

                issues.append({

                    "issue": issue_name,

                    "matches_found": len(matches)
                })

        return {

            "success": True,

            "safe": len(issues) == 0,

            "issues": issues
        }


# global helper 

security_checker = (
    SecurityCheckerTool()
)