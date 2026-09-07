"""
Read-only workspace browsing for the desktop app's file tree.

Deliberately separate from tools/code_tools/file_reader.py's FileReaderTool:
that one is an agent-facing tool (bounded to PROJECT_ROOT/GENERATED_PROJECT_DIR,
denies sensitive filenames outright). This is a server-facing browser for a
human looking at whatever workspace they've pointed the desktop app at —
same path-traversal discipline, but scoped to a caller-supplied root rather
than a fixed pair of allowed roots, since "which project is open" is a
per-session choice the user makes, not a constant.
"""
from pathlib import Path
from typing import Any, Dict, List

#same sensitive-filename list as tools/code_tools/file_reader.py — a
#human browsing files shouldn't see secrets any more than an agent should
DENIED_FILENAMES = {
    ".env",
    ".env.local",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
}

#directories never worth showing in a file tree — build artifacts, VCS
#internals, dependency trees. Kept short and generic on purpose.
DENIED_DIRNAMES = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
}

#skip obviously-binary files in the tree — the desktop app has no viewer
#for them yet, and a raw byte dump isn't useful in a text-only read_file
_BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".tar", ".gz",
    ".pyc", ".so", ".woff", ".woff2", ".ttf", ".db", ".sqlite", ".sqlite3",
}


class WorkspaceError(Exception):
    """Raised for anything that isn't a normal 'file not found' — path escapes, denied names."""


def _resolve_within_root(root: Path, relative: str) -> Path:
    """
    Resolve `relative` against `root`, refusing anything that escapes it
    (via `..`, an absolute path, or a symlink) — path-traversal protection
    for a browser that takes its path from an HTTP query parameter.
    """
    root = root.expanduser().resolve()
    candidate = (root / relative).expanduser().resolve() if relative else root

    if not (candidate == root or candidate.is_relative_to(root)):
        raise WorkspaceError(f"Path '{relative}' escapes the workspace root.")

    if candidate.name in DENIED_FILENAMES:
        raise WorkspaceError(f"Refusing to expose '{relative}': sensitive filename.")

    return candidate


def list_directory(root: Path, relative: str = "") -> List[Dict[str, Any]]:
    """
    List the immediate children of `relative` (within `root`), directories
    first then files, both alphabetical. Raises WorkspaceError if the path
    escapes `root`, FileNotFoundError if it doesn't exist, NotADirectoryError
    if it's a file.
    """
    target = _resolve_within_root(root, relative)

    if not target.exists():
        raise FileNotFoundError(f"No such path in workspace: {relative or '.'}")
    if not target.is_dir():
        raise NotADirectoryError(f"Not a directory: {relative or '.'}")

    entries = []
    for child in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        if child.is_dir() and child.name in DENIED_DIRNAMES:
            continue
        if child.name in DENIED_FILENAMES:
            continue

        entries.append({
            "name": child.name,
            "path": str(child.relative_to(root)),
            "is_dir": child.is_dir(),
        })

    return entries


def read_file(root: Path, relative: str) -> str:
    """
    Read a text file's content, scoped within `root`. Raises WorkspaceError
    for a path that escapes root, a denied filename, or a binary-looking
    extension the desktop app has no viewer for.
    """
    target = _resolve_within_root(root, relative)

    if target.suffix.lower() in _BINARY_SUFFIXES:
        raise WorkspaceError(f"Refusing to read binary-looking file: {relative}")

    if not target.exists():
        raise FileNotFoundError(f"No such file in workspace: {relative}")
    if not target.is_file():
        raise IsADirectoryError(f"Not a file: {relative}")

    try:
        return target.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise WorkspaceError(f"'{relative}' is not valid UTF-8 text.") from e
