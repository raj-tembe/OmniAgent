from pathlib import Path
from typing import Dict

from tools.code_tools.file_reader import _resolve_allowed_path


class EditTool:
    """
    Structured, diff-based file editing: replace one exact, unique
    occurrence of `old_str` with `new_str`, rather than rewriting the whole
    file (what FileWriterTool.write_file does). This is the gap between
    "regenerate the whole file" and "change one thing" — safer for small
    fixes because a non-unique or missing match fails loudly instead of
    silently overwriting unrelated content.
    """

    @staticmethod
    def apply_edit(filepath: str, old_str: str, new_str: str) -> Dict:
        """
        Replace the single occurrence of `old_str` in `filepath` with
        `new_str`. Fails if `old_str` matches zero or more than one place —
        callers should widen `old_str` with surrounding context until it's
        unique, same discipline as any find-and-replace edit tool.
        """
        try:
            safe_path = _resolve_allowed_path(filepath)
            content = safe_path.read_text(encoding="utf-8")

            occurrences = content.count(old_str)
            if occurrences == 0:
                return {
                    "success": False,
                    "filepath": str(safe_path),
                    "error": "old_str not found in file.",
                }
            if occurrences > 1:
                return {
                    "success": False,
                    "filepath": str(safe_path),
                    "error": f"old_str is not unique ({occurrences} matches) — widen it with more surrounding context.",
                }

            updated = content.replace(old_str, new_str, 1)
            safe_path.write_text(updated, encoding="utf-8")

            return {
                "success": True,
                "filepath": str(safe_path),
                "bytes_written": len(updated),
            }

        except Exception as e:
            return {
                "success": False,
                "filepath": filepath,
                "error": str(e),
            }
