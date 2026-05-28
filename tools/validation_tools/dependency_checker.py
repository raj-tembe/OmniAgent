import importlib
import re
from typing import Dict, List


# dependencies checker tool

class DependencyCheckerTool:
    """
    Dependency validation tool.

    Responsibilities:
    - detect imported packages
    - validate installed dependencies
    - identify missing requirements
    """


    # extract import

    @staticmethod
    def extract_imports(
        code: str
    ) -> List[str]:
        """
        Extract imported modules from Python code.
        """

        imports = set()

        import_patterns = [

            r"import\s+([a-zA-Z0-9_]+)",

            r"from\s+([a-zA-Z0-9_]+)"
        ]

        for pattern in import_patterns:

            matches = re.findall(
                pattern,
                code
            )

            imports.update(matches)

        return list(imports)


    # check dependencies

    @staticmethod
    def check_dependencies(
        code: str
    ) -> Dict:
        """
        Validate imported dependencies.
        """

        imports = (
            DependencyCheckerTool
            .extract_imports(code)
        )

        installed = []

        missing = []

        for module in imports:

            try:

                importlib.import_module(module)

                installed.append(module)

            except ImportError:

                missing.append(module)

        return {

            "success": True,

            "imports": imports,

            "installed": installed,

            "missing": missing,

            "all_dependencies_available": (
                len(missing) == 0
            )
        }


# global helper 

dependency_checker = (
    DependencyCheckerTool()
)