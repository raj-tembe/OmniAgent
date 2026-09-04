"""
Diffing between two `generated_files` snapshots (coder_agent's before/after).

Kept standalone from coder_agent.py so it's trivially unit-testable without
touching the LLM chain — pure functions in, structured diffs out.
"""
import difflib
from typing import Dict, List, TypedDict


class FileDiffResult(TypedDict):
    filename: str
    change_type: str  # "added" | "modified"
    diff: str


def compute_file_diffs(before: Dict[str, str], after: Dict[str, str]) -> List[FileDiffResult]:
    """
    Compare `before` and `after` (both filename -> content) and return a
    unified diff for every file that's new or changed. Deleted files and
    unchanged files are both omitted — deletion isn't something
    coder_agent currently does (it only ever adds/modifies files in
    `generated_files`), and an unchanged file has nothing to show.
    """
    results: List[FileDiffResult] = []

    for filename, new_content in after.items():
        old_content = before.get(filename)

        if old_content is None:
            change_type = "added"
            old_lines = []
        elif old_content == new_content:
            continue
        else:
            change_type = "modified"
            old_lines = old_content.splitlines(keepends=True)

        new_lines = new_content.splitlines(keepends=True)

        diff_lines = list(difflib.unified_diff(
            old_lines, new_lines,
            fromfile=f"a/{filename}", tofile=f"b/{filename}",
        ))

        results.append({
            "filename": filename,
            "change_type": change_type,
            "diff": "".join(diff_lines),
        })

    return results
