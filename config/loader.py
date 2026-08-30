"""
Loads and merges OmniAgent's declarative config file.

Resolution order (later overrides earlier):
    1. schema defaults
    2. global config: ~/.config/omniagent/omniagent.json (or $OMNIAGENT_CONFIG_DIR)
    3. project config: `omniagent.json` found by walking up from the current
       working directory until a `.git` directory is found (or the
       filesystem root is reached)

Both files are optional — a missing file just means "use defaults for this
layer". Malformed JSON raises rather than silently ignoring it, since a
typo'd permission rule silently not applying is a safety problem for
Phase 1's permission engine, not just a config nicety.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from config.schema import OmniAgentConfig

CONFIG_FILENAME = "omniagent.json"


def _global_config_dir() -> Path:
    override = os.getenv("OMNIAGENT_CONFIG_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / ".config" / "omniagent"


def _find_project_config(start: Optional[Path] = None) -> Optional[Path]:
    """
    Walk up from `start` (default: cwd) looking for `omniagent.json`, stopping
    after checking the directory that contains `.git`.
    """
    current = (start or Path.cwd()).resolve()

    while True:
        candidate = current / CONFIG_FILENAME
        if candidate.is_file():
            return candidate

        if (current / ".git").exists():
            return None

        if current.parent == current:
            return None

        current = current.parent


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge `override` into `base`. Dicts merge key-by-key; lists
    and scalars are replaced outright (a project's `plugin` list fully
    replaces the global one rather than deduping/concatenating — explicit
    and easy to reason about).
    """
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(project_start: Optional[Path] = None) -> OmniAgentConfig:
    """
    Load and merge global + project config into a validated OmniAgentConfig.
    """
    merged: Dict[str, Any] = {}

    global_path = _global_config_dir() / CONFIG_FILENAME
    if global_path.is_file():
        merged = _deep_merge(merged, _load_json(global_path))

    project_path = _find_project_config(project_start)
    if project_path is not None:
        merged = _deep_merge(merged, _load_json(project_path))

    return OmniAgentConfig.model_validate(merged)


def config_paths(project_start: Optional[Path] = None) -> Dict[str, Optional[Path]]:
    """
    Report which config files (if any) `load_config` would read — useful for
    a future `omniagent config` diagnostic command.
    """
    global_path = _global_config_dir() / CONFIG_FILENAME
    return {
        "global": global_path if global_path.is_file() else None,
        "project": _find_project_config(project_start),
    }
