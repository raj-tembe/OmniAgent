"""
Which language server to launch for a given file extension.

Only servers that are simple to install and run headless (no editor-specific
setup) are listed. A missing entry means "no diagnostics support for this
file type yet" — lsp/client.py treats that as a clear, explicit error rather
than silently returning no diagnostics, so a caller can tell "the server
isn't configured" apart from "the server ran and found nothing wrong".
"""
from typing import Dict, List, Optional

SERVER_COMMANDS: Dict[str, List[str]] = {
    ".py": ["pylsp"],
    ".pyi": ["pylsp"],
    ".ts": ["typescript-language-server", "--stdio"],
    ".tsx": ["typescript-language-server", "--stdio"],
    ".js": ["typescript-language-server", "--stdio"],
    ".jsx": ["typescript-language-server", "--stdio"],
    ".go": ["gopls"],
    ".rs": ["rust-analyzer"],
}

LANGUAGE_IDS: Dict[str, str] = {
    ".py": "python",
    ".pyi": "python",
    ".ts": "typescript",
    ".tsx": "typescriptreact",
    ".js": "javascript",
    ".jsx": "javascriptreact",
    ".go": "go",
    ".rs": "rust",
}


def get_server_command(suffix: str) -> Optional[List[str]]:
    """The command to launch for `suffix` (e.g. ".py"), or None if unsupported."""
    return SERVER_COMMANDS.get(suffix)


def get_language_id(suffix: str) -> str:
    """The LSP languageId for `suffix`, defaulting to 'plaintext' if unknown."""
    return LANGUAGE_IDS.get(suffix, "plaintext")


def supported_extensions() -> List[str]:
    return sorted(SERVER_COMMANDS)
