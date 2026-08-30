import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from config.loader import _deep_merge, _find_project_config, config_paths, load_config


class TestDeepMerge(unittest.TestCase):

    def test_nested_dicts_merge_key_by_key(self):
        base = {"permission": {"rules": {"bash": "ask"}, "auto": False}}
        override = {"permission": {"rules": {"edit": "deny"}}}

        merged = _deep_merge(base, override)

        self.assertEqual(merged["permission"]["rules"], {"bash": "ask", "edit": "deny"})
        self.assertFalse(merged["permission"]["auto"])

    def test_lists_are_replaced_not_concatenated(self):
        base = {"plugin": ["a", "b"]}
        override = {"plugin": ["c"]}

        merged = _deep_merge(base, override)

        self.assertEqual(merged["plugin"], ["c"])

    def test_scalar_override_wins(self):
        base = {"permission": {"auto": False}}
        override = {"permission": {"auto": True}}

        merged = _deep_merge(base, override)

        self.assertTrue(merged["permission"]["auto"])


class TestFindProjectConfig(unittest.TestCase):

    def test_finds_config_in_cwd(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            (root / "omniagent.json").write_text("{}")

            found = _find_project_config(root)

            self.assertEqual(found, root / "omniagent.json")

    def test_walks_up_to_git_root(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            (root / "omniagent.json").write_text("{}")
            nested = root / "src" / "deep" / "nested"
            nested.mkdir(parents=True)

            found = _find_project_config(nested)

            self.assertEqual(found, root / "omniagent.json")

    def test_returns_none_when_no_config_found(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()

            found = _find_project_config(root)

            self.assertIsNone(found)

    def test_stops_at_git_root_even_if_none_found_there(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            nested = root / "pkg"
            nested.mkdir()

            found = _find_project_config(nested)

            self.assertIsNone(found)


class TestLoadConfig(unittest.TestCase):

    def test_project_overrides_global(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()

            global_dir = root / "global-config"
            global_dir.mkdir()
            (global_dir / "omniagent.json").write_text(json.dumps({
                "permission": {"rules": {"bash": "ask"}},
            }))

            (root / "omniagent.json").write_text(json.dumps({
                "permission": {"rules": {"bash": "allow"}},
            }))

            with patch.dict("os.environ", {"OMNIAGENT_CONFIG_DIR": str(global_dir)}):
                cfg = load_config(project_start=root)

            self.assertEqual(cfg.permission.rules["bash"], "allow")

    def test_missing_files_produce_defaults(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()

            with patch.dict("os.environ", {"OMNIAGENT_CONFIG_DIR": str(root / "nonexistent")}):
                cfg = load_config(project_start=root)

            self.assertEqual(cfg.permission.rules, {})

    def test_config_paths_reports_none_for_missing_files(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()

            with patch.dict("os.environ", {"OMNIAGENT_CONFIG_DIR": str(root / "nonexistent")}):
                paths = config_paths(project_start=root)

            self.assertIsNone(paths["global"])
            self.assertIsNone(paths["project"])


if __name__ == "__main__":
    unittest.main()
