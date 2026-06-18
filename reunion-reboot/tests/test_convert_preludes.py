import subprocess
import unittest
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]


class ConvertPreludesTests(unittest.TestCase):
    def test_generated_preludes_page_removes_title_area(self):
        result = subprocess.run(
            ["python3", "convert_preludes.py"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)

        html = (BASE_DIR / "html" / "preludes.html").read_text(encoding="utf-8")
        self.assertNotIn("<h1>삽화</h1>", html)
        self.assertNotIn('class="page-sub"', html)
        self.assertNotIn('class="section-title"', html)
        self.assertIn('class="gallery-track"', html)
        self.assertNotIn("ep.209", html)

    def test_generated_preludes_page_groups_by_episode_range(self):
        result = subprocess.run(
            ["python3", "convert_preludes.py"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)

        html = (BASE_DIR / "html" / "preludes.html").read_text(encoding="utf-8")
        self.assertIn('class="range-tabs"', html)
        self.assertIn('data-range-target="001-100"', html)
        self.assertIn('data-range-target="101-200"', html)
        self.assertIn('data-range-target="201-300"', html)
        self.assertIn('class="range-panel active" data-range-panel="301-400"', html)

    def test_generated_preludes_page_scrolls_one_image_at_a_time(self):
        result = subprocess.run(
            ["python3", "convert_preludes.py"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)

        html = (BASE_DIR / "html" / "preludes.html").read_text(encoding="utf-8")
        self.assertIn("scrollToItem(track, nextIndex);", html)
        self.assertIn("event.preventDefault();", html)
        self.assertIn("track.addEventListener('wheel'", html)
        self.assertIn("scroll-snap-type: y mandatory;", html)
        self.assertIn("min-height: 100%;", html)


if __name__ == "__main__":
    unittest.main()
