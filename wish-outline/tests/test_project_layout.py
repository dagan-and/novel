from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ProjectLayoutTests(unittest.TestCase):
    def test_runtime_files_use_the_clean_project_layout(self):
        expected_paths = [
            "generate_outlines.py",
            "characters",
            "profiles",
            "prompts/outline.txt",
            "prompts/image.txt",
            "outlines",
            "tools/append_footer.py",
            "tools/remove_footer.py",
            "tools/push_outlines.py",
            "tools/footer_keywords.json",
        ]

        for relative_path in expected_paths:
            with self.subTest(path=relative_path):
                self.assertTrue((PROJECT_ROOT / relative_path).exists())

    def test_obsolete_instruction_tree_is_removed(self):
        obsolete_paths = [
            "00_INDEX.txt",
            "AGENTS.txt",
            "CLAUDE.txt",
            "00_core",
            "01_world",
            "02_characters",
            "03_story_state",
            "05_outline",
            "outline_profiles",
        ]

        for relative_path in obsolete_paths:
            with self.subTest(path=relative_path):
                self.assertFalse((PROJECT_ROOT / relative_path).exists())


if __name__ == "__main__":
    unittest.main()
