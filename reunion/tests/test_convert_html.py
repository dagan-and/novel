import shutil
import subprocess
import unittest
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
EPISODE_PATH = BASE_DIR / "episodes" / "ep.998_a.md"
IMAGE_DIR = BASE_DIR / "images" / "preludes"
IMAGE_PATH = IMAGE_DIR / "ep.998.png"
HTML_PATH = BASE_DIR / "html" / "ep.998_a.html"


class ConvertHtmlIllustrationTests(unittest.TestCase):
    def tearDown(self):
        for path in (EPISODE_PATH, IMAGE_PATH, HTML_PATH):
            if path.exists():
                path.unlink()

        if IMAGE_DIR.exists() and not any(IMAGE_DIR.iterdir()):
            IMAGE_DIR.rmdir()

    def test_adult_episode_with_prelude_image_renders_html_illustration(self):
        IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        EPISODE_PATH.write_text(
            "\n".join(
                [
                    "샘플 본문 첫 문장.",
                    "",
                    "---",
                    "## [성인씬 #1 — ep.998]",
                    "",
                    "- 장소: 테스트 공간",
                    "- <progress>3단계</progress>",
                    "",
                    "---",
                    "",
                    "후속 문장.",
                ]
            ),
            encoding="utf-8",
        )
        shutil.copyfile(BASE_DIR / "images" / "characters" / "임소율.png", IMAGE_PATH)

        result = subprocess.run(
            ["python3", "convert_html.py", "ep.998_a"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(HTML_PATH.exists(), msg=result.stdout)

        html = HTML_PATH.read_text(encoding="utf-8")
        self.assertIn('class="scene-illustration"', html)
        self.assertIn("../images/preludes/ep.998.png", html)
        self.assertIn("<figcaption>테스트 공간</figcaption>", html)
        self.assertNotIn("## [성인씬 #1 — ep.998]", html)


if __name__ == "__main__":
    unittest.main()
