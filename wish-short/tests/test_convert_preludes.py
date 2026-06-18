import subprocess
import unittest
import base64
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
PRELUDE_PATH = BASE_DIR / "images" / "preludes" / "001-100" / "ep.001.png"
HTML_PATH = BASE_DIR / "html" / "preludes.html"
TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


class ConvertPreludesTests(unittest.TestCase):
    def setUp(self):
        PRELUDE_PATH.parent.mkdir(parents=True, exist_ok=True)
        PRELUDE_PATH.write_bytes(TINY_PNG)

    def tearDown(self):
        if PRELUDE_PATH.exists():
            PRELUDE_PATH.unlink()
        if PRELUDE_PATH.parent.exists() and not any(PRELUDE_PATH.parent.iterdir()):
            PRELUDE_PATH.parent.rmdir()

    def test_generated_preludes_page_removes_title_area(self):
        result = subprocess.run(
            ["python3", "convert_preludes.py"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)

        html = HTML_PATH.read_text(encoding="utf-8")
        self.assertNotIn("<h1>삽화</h1>", html)
        self.assertNotIn('class="page-sub"', html)
        self.assertNotIn('class="section-title"', html)
        self.assertIn('class="gallery-track"', html)
        self.assertIn("ep.001", html)

    def test_generated_preludes_page_groups_by_episode_range(self):
        result = subprocess.run(
            ["python3", "convert_preludes.py"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)

        html = HTML_PATH.read_text(encoding="utf-8")
        self.assertIn('class="range-tabs"', html)
        self.assertIn('data-range-target="001-100"', html)
        self.assertIn('data-range-panel="001-100"', html)
        self.assertIn('class="range-panel active"', html)

    def test_generated_preludes_page_scrolls_one_image_at_a_time(self):
        result = subprocess.run(
            ["python3", "convert_preludes.py"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)

        html = HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("scrollToItem(track, nextIndex);", html)
        self.assertIn("event.preventDefault();", html)
        self.assertIn("track.addEventListener('wheel'", html)
        self.assertIn("scroll-snap-type: y mandatory;", html)
        self.assertIn("min-height: 100%;", html)


if __name__ == "__main__":
    unittest.main()
