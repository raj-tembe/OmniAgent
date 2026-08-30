import re
from pathlib import Path
from typing import Dict, List, Optional

from config import PROJECT_ROOT
from tools.code_tools.file_reader import DENIED_FILENAMES, _resolve_allowed_path

#skip obviously-binary/large-generated files rather than trying to grep them
_SKIP_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".tar", ".gz",
    ".pyc", ".so", ".woff", ".woff2", ".ttf", ".db", ".sqlite", ".sqlite3",
}


class GrepTool:
    """
    Fast content search across the project, scoped to the allowed roots.

    This is the "find where X is used/defined" tool the agents currently
    lack — FileReaderTool can only read files it's already been told about,
    it can't discover them by content.
    """

    @staticmethod
    def search(
        pattern: str,
        directory: Optional[str] = None,
        file_glob: str = "**/*",
        regex: bool = True,
        max_results: int = 200,
    ) -> Dict:
        """
        Search file contents under `directory` (default: PROJECT_ROOT) for
        `pattern`. Set regex=False to search for a literal substring
        instead of treating `pattern` as a regular expression.
        """
        try:
            base = _resolve_allowed_path(directory or PROJECT_ROOT)
            matcher = re.compile(pattern) if regex else None

            results: List[Dict] = []
            for path in base.glob(file_glob):
                if not path.is_file():
                    continue
                if any(part.startswith(".") for part in path.relative_to(base).parts[:-1]):
                    continue
                if path.name in DENIED_FILENAMES or path.suffix.lower() in _SKIP_SUFFIXES:
                    continue

                try:
                    text = path.read_text(encoding="utf-8")
                except (UnicodeDecodeError, OSError):
                    continue

                for line_number, line in enumerate(text.splitlines(), start=1):
                    hit = matcher.search(line) if matcher else (pattern in line)
                    if hit:
                        results.append({
                            "file": str(path),
                            "line_number": line_number,
                            "line": line.strip(),
                        })
                        if len(results) >= max_results:
                            break

                if len(results) >= max_results:
                    break

            return {
                "success": True,
                "pattern": pattern,
                "matches": results,
                "truncated": len(results) >= max_results,
            }

        except re.error as e:
            return {"success": False, "pattern": pattern, "error": f"Invalid regex: {e}"}
        except Exception as e:
            return {"success": False, "pattern": pattern, "error": str(e)}
