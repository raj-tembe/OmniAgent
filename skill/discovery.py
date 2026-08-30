"""
Discovers `SKILL.md` files: one folder per skill name, a required YAML
frontmatter with `name` and `description`, searched across a project-local
set of directories (walked up to the git root) and a global set under the
user's home directory.

This intentionally reads the same directory conventions Claude Code and
other coding-agent tools use (`.claude/skills/`, `.agents/skills/`) in
addition to OmniAgent's own `.omniagent/skills/`, so a skill written for one
tool works with all of them.
"""
import logging
from pathlib import Path
from typing import List, Literal, Optional

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

#directory names checked at each project level, and under the home directory,
#in this order.
_PROJECT_SKILL_DIRS = (".omniagent/skills", ".claude/skills", ".agents/skills")
_GLOBAL_SKILL_DIRS = (
    "~/.config/omniagent/skills",
    "~/.claude/skills",
    "~/.agents/skills",
)


class SkillMetadata(BaseModel):
    """
    Discovered skill, without its full body loaded yet — see skill/loader.py
    for reading the full SKILL.md content on demand.
    """

    name: str = Field(..., description="Skill name from SKILL.md frontmatter.")
    description: str = Field(..., description="One-line description from SKILL.md frontmatter.")
    path: Path = Field(..., description="Path to the skill's SKILL.md file.")
    source: Literal["project", "global"] = Field(..., description="Whether this came from a project or global skills directory.")


def _parse_frontmatter(path: Path) -> Optional[dict]:
    """
    Parse the leading `---\\n...\\n---` YAML block of a SKILL.md file.
    Returns None (and logs) if the file is missing the block or required
    fields — a malformed skill is skipped, not fatal to discovery.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("Could not read skill file %s: %s", path, exc)
        return None

    if not text.startswith("---"):
        logger.warning("Skill file %s has no frontmatter block; skipping.", path)
        return None

    parts = text.split("---", 2)
    if len(parts) < 3:
        logger.warning("Skill file %s has an unterminated frontmatter block; skipping.", path)
        return None

    try:
        frontmatter = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as exc:
        logger.warning("Skill file %s has invalid YAML frontmatter: %s", path, exc)
        return None

    if "name" not in frontmatter or "description" not in frontmatter:
        logger.warning("Skill file %s is missing required 'name' or 'description'; skipping.", path)
        return None

    return frontmatter


def _walk_project_roots(start: Path) -> List[Path]:
    """
    Every directory from `start` up to (and including) the one containing
    `.git`, closest-first.
    """
    roots = []
    current = start.resolve()
    while True:
        roots.append(current)
        if (current / ".git").exists():
            break
        if current.parent == current:
            break
        current = current.parent
    return roots


def _scan_skill_dir(skill_dir: Path, source: Literal["project", "global"]) -> List[SkillMetadata]:
    if not skill_dir.is_dir():
        return []

    found = []
    for entry in sorted(skill_dir.iterdir()):
        skill_file = entry / "SKILL.md"
        if not skill_file.is_file():
            continue

        frontmatter = _parse_frontmatter(skill_file)
        if frontmatter is None:
            continue

        found.append(SkillMetadata(
            name=str(frontmatter["name"]),
            description=str(frontmatter["description"]),
            path=skill_file,
            source=source,
        ))

    return found


def discover_skills(start: Optional[Path] = None) -> List[SkillMetadata]:
    """
    Discover every available skill: project-local directories (walked up to
    the git root) first, then global directories. If a project skill and a
    global skill share a name, the project one is kept and the global
    duplicate is dropped — project-local should win.
    """
    start = start or Path.cwd()
    discovered: List[SkillMetadata] = []
    seen_names = set()

    for root in _walk_project_roots(start):
        for dirname in _PROJECT_SKILL_DIRS:
            for skill in _scan_skill_dir(root / dirname, source="project"):
                if skill.name not in seen_names:
                    discovered.append(skill)
                    seen_names.add(skill.name)

    for dirname in _GLOBAL_SKILL_DIRS:
        for skill in _scan_skill_dir(Path(dirname).expanduser(), source="global"):
            if skill.name not in seen_names:
                discovered.append(skill)
                seen_names.add(skill.name)

    return discovered
