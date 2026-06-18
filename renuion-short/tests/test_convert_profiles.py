import re
import subprocess
import unittest
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]


class ConvertProfilesAdultSceneTests(unittest.TestCase):
    def render_profile(self, name):
        result = subprocess.run(
            ["python3", "convert_profiles.py", name],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        html_path = BASE_DIR / "html" / "characters" / f"{name}.html"
        self.assertTrue(html_path.exists(), msg=result.stdout)
        return html_path.read_text(encoding="utf-8")

    def test_profile_shows_compact_heart_count_without_adult_scene_copy(self):
        html = self.render_profile("박미현")

        count_match = re.search(r'class="adult-scene-count">♥\s*(\d+)</p>', html)
        self.assertIsNotNone(count_match)
        displayed_total = int(count_match.group(1))
        self.assertEqual(len(re.findall(r'class="heart filled"', html)), displayed_total)
        expected_empty = 1 if displayed_total == 0 else 0
        self.assertEqual(len(re.findall(r'class="heart empty"', html)), expected_empty)
        self.assertNotIn('class="adult-scene-label"', html)
        self.assertNotIn("성인씬 9회", html)
        self.assertNotIn("친밀도:", html)
        self.assertNotIn("관계 진도:", html)
        self.assertNotIn("현재 단계:", html)

    def test_profile_keeps_heart_count_in_sync_with_displayed_total(self):
        html = self.render_profile("유하린")

        count_match = re.search(r'class="adult-scene-count">♥\s*(\d+)</p>', html)
        self.assertIsNotNone(count_match)
        displayed_total = int(count_match.group(1))
        self.assertEqual(len(re.findall(r'class="heart filled"', html)), displayed_total)
        expected_empty = 1 if displayed_total == 0 else 0
        self.assertEqual(len(re.findall(r'class="heart empty"', html)), expected_empty)

    def test_profile_renders_origin_without_series_title(self):
        html = self.render_profile("서나윤")

        self.assertIn("출신: 서울", html)
        self.assertNotIn("다시 만나는 관계들", html)

    def test_character_index_uses_three_by_two_expanded_grid(self):
        result = subprocess.run(
            ["python3", "convert_profiles.py", "all"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)

        html = (BASE_DIR / "html" / "characters.html").read_text(encoding="utf-8")
        self.assertIn("grid-template-columns: repeat(3, minmax(0, 1fr));", html)
        self.assertIn("grid-template-rows: repeat(2, minmax(0, 1fr));", html)
        self.assertIn("height: 100svh;", html)
        self.assertIn("height: 100dvh;", html)
        self.assertIn("env(safe-area-inset-bottom)", html)
        self.assertNotIn("grid-template-columns: repeat(2", html)
        self.assertNotIn("grid-template-columns: 1fr", html)
        self.assertNotIn('href="characters/김시안.html"', html)
        self.assertEqual(html.count('class="card"'), 6)

    def test_character_index_labels_have_readability_treatment(self):
        result = subprocess.run(
            ["python3", "convert_profiles.py", "all"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)

        html = (BASE_DIR / "html" / "characters.html").read_text(encoding="utf-8")
        self.assertIn("-webkit-text-stroke: 0.45px rgba(0,0,0,0.9);", html)
        self.assertIn("text-shadow: 0 1px 2px rgba(0,0,0,1), 0 3px 12px rgba(0,0,0,0.95);", html)
        self.assertIn("linear-gradient(180deg, rgba(17,20,23,0) 22%, rgba(17,20,23,0.72) 70%, rgba(17,20,23,0.96) 100%)", html)


if __name__ == "__main__":
    unittest.main()
