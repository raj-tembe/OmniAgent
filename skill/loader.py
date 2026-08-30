"""
Loads a skill's full body on demand, and formats discovered skills for
injection into an agent's prompt.

Skills are loaded lazily by design: discover_skills() only reads frontmatter
(cheap, safe to run on every planner turn), and load_skill() reads the full
body only once an agent actually decides to use a specific skill — same
"see the list, load on demand" model.
"""
import logging
from typing import List, Optional

from skill.discovery import SkillMetadata, discover_skills

logger = logging.getLogger(__name__)


class SkillNotFoundError(Exception):
    """Raised when load_skill() is asked for a name that discovery didn't find."""


def load_skill(name: str, start=None) -> str:
    """
    Return the full SKILL.md content (frontmatter included) for the skill
    named `name`. Re-runs discovery so a skill added mid-session is picked
    up without restarting the process.
    """
    skills = discover_skills(start=start)
    match = next((s for s in skills if s.name == name), None)

    if match is None:
        raise SkillNotFoundError(f"No skill named '{name}' found.")

    return match.path.read_text(encoding="utf-8")


def format_skill_list(skills: Optional[List[SkillMetadata]] = None, start=None) -> str:
    """
    Render discovered skills as a short "name: description" list suitable
    for dropping into an agent's system prompt. Returns a "no skills
    available" placeholder rather than an empty string so the prompt template
    always has something sensible to show.
    """
    if skills is None:
        skills = discover_skills(start=start)

    if not skills:
        return "(no skills available)"

    return "\n".join(f"- {s.name}: {s.description}" for s in skills)
