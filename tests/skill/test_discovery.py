import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from skill.discovery import discover_skills
from skill.loader import SkillNotFoundError, format_skill_list, load_skill


def _write_skill(base: Path, subdir: str, name: str, description: str, body: str = "Do the thing.") -> None:
    skill_dir = base / subdir / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n{body}\n"
    )


class TestDiscoverSkills(unittest.TestCase):

    def test_finds_skill_in_omniagent_dir(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            _write_skill(root, ".omniagent/skills", "commit-messages", "Write good commit messages.")

            found = discover_skills(start=root)

            self.assertEqual(len(found), 1)
            self.assertEqual(found[0].name, "commit-messages")
            self.assertEqual(found[0].source, "project")

    def test_finds_skill_in_claude_compatible_dir(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            _write_skill(root, ".claude/skills", "pdf-reading", "Read PDFs.")

            found = discover_skills(start=root)

            self.assertEqual([s.name for s in found], ["pdf-reading"])

    def test_walks_up_to_git_root(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            _write_skill(root, ".omniagent/skills", "root-skill", "At the root.")
            nested = root / "src" / "deep"
            nested.mkdir(parents=True)

            found = discover_skills(start=nested)

            self.assertEqual([s.name for s in found], ["root-skill"])

    def test_missing_frontmatter_fields_are_skipped(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            skill_dir = root / ".omniagent" / "skills" / "broken"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("---\nname: broken\n---\nNo description.\n")

            found = discover_skills(start=root)

            self.assertEqual(found, [])

    def test_no_frontmatter_block_is_skipped(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            skill_dir = root / ".omniagent" / "skills" / "broken"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("Just a plain markdown file, no frontmatter.\n")

            found = discover_skills(start=root)

            self.assertEqual(found, [])

    def test_project_skill_wins_over_global_duplicate(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            _write_skill(root, ".omniagent/skills", "shared-name", "Project version.")

            global_dir = root / "global"
            _write_skill(global_dir, "skills", "shared-name", "Global version.")

            with patch("skill.discovery._GLOBAL_SKILL_DIRS", (str(global_dir / "skills"),)):
                found = discover_skills(start=root)

            self.assertEqual(len(found), 1)
            self.assertEqual(found[0].description, "Project version.")
            self.assertEqual(found[0].source, "project")


class TestLoadSkill(unittest.TestCase):

    def test_loads_full_body(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            _write_skill(root, ".omniagent/skills", "my-skill", "Does a thing.", body="Full instructions here.")

            content = load_skill("my-skill", start=root)

            self.assertIn("Full instructions here.", content)
            self.assertIn("name: my-skill", content)

    def test_raises_for_unknown_skill(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()

            with self.assertRaises(SkillNotFoundError):
                load_skill("does-not-exist", start=root)


class TestFormatSkillList(unittest.TestCase):

    def test_formats_discovered_skills(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            _write_skill(root, ".omniagent/skills", "a", "Does A.")
            _write_skill(root, ".omniagent/skills", "b", "Does B.")

            formatted = format_skill_list(start=root)

            self.assertIn("- a: Does A.", formatted)
            self.assertIn("- b: Does B.", formatted)

    def test_empty_list_has_placeholder(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()

            formatted = format_skill_list(start=root)

            self.assertEqual(formatted, "(no skills available)")


if __name__ == "__main__":
    unittest.main()
