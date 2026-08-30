import fnmatch
import os
from pathlib import Path
from typing import Dict, List, Optional

from config import GENERATED_PROJECT_DIR, PROJECT_ROOT
from tools.code_tools.file_reader import DENIED_FILENAMES, _resolve_allowed_path


class GlobTool:
    """
    Fast filename pattern matching, scoped to the allowed project roots.

    Complements FileReaderTool.list_files (which lists everything) with a
    targeted "find files matching this pattern" search — the difference
    between listing a whole tree and finding "**/*.py" or "src/**/test_*.py"
    in one call.
    """

    @staticmethod
    def find(
        pattern: str,
        directory: Optional[str] = None,
        max_results: int = 500,
    ) -> Dict:
        """
        Find files under `directory` (default: PROJECT_ROOT) matching the
        glob `pattern` (e.g. "**/*.py", "src/**/test_*.py"). Hidden
        directories and denied filenames are skipped.
        """
        try:
            base = _resolve_allowed_path(directory or PROJECT_ROOT)

            matches: List[str] = []
            for path in base.glob(pattern):
                if not path.is_file():
                    continue
                if any(part.startswith(".") for part in path.relative_to(base).parts[:-1]):
                    continue
                if path.name in DENIED_FILENAMES:
                    continue

                matches.append(str(path))
                if len(matches) >= max_results:
                    break

            return {
                "success": True,
                "pattern": pattern,
                "matches": matches,
                "truncated": len(matches) >= max_results,
            }

        except Exception as e:
            return {
                "success": False,
                "pattern": pattern,
                "error": str(e),
            }
