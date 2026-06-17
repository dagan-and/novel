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


if __name__ == "__main__":
    unittest.main()
