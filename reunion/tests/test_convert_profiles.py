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

    def test_profile_shows_adult_scene_hearts_and_count(self):
        html = self.render_profile("정다온")

        count_match = re.search(r"성인씬 (\d+)회", html)
        self.assertIsNotNone(count_match)
        self.assertEqual(len(re.findall(r'class="heart filled"', html)), int(count_match.group(1)))
        self.assertEqual(len(re.findall(r'class="heart empty"', html)), 0)
        self.assertNotIn("친밀도:", html)
        self.assertNotIn("관계 진도:", html)
        self.assertNotIn("현재 단계:", html)

    def test_profile_keeps_heart_count_in_sync_with_displayed_total(self):
        html = self.render_profile("이하은")

        count_match = re.search(r"성인씬 (\d+)회", html)
        self.assertIsNotNone(count_match)
        self.assertEqual(len(re.findall(r'class="heart filled"', html)), int(count_match.group(1)))
        self.assertEqual(len(re.findall(r'class="heart empty"', html)), 0)

    def test_profile_renders_origin_without_series_title(self):
        html = self.render_profile("임소율")

        self.assertIn("출신: 부산", html)
        self.assertNotIn("다시 만나는 관계들", html)


if __name__ == "__main__":
    unittest.main()
