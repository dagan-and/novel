import shutil
import subprocess
import unittest
from pathlib import Path

from batch_paths import html_episode_path, prelude_output_path


BASE_DIR = Path(__file__).resolve().parents[1]
EPISODE_PATH = BASE_DIR / "episodes" / "901-1000" / "ep.998_a.md"
IMAGE_DIR = BASE_DIR / "images" / "preludes" / "901-1000"
IMAGE_PATH = prelude_output_path(BASE_DIR, "ep.998", "png")
HTML_PATH = html_episode_path(BASE_DIR, "ep.998_a")


class ConvertHtmlIllustrationTests(unittest.TestCase):
    def tearDown(self):
        for path in (
            EPISODE_PATH,
            BASE_DIR / "episodes" / "901-1000" / "ep.999.md",
            BASE_DIR / "episodes" / "901-1000" / "ep.1000.md",
            BASE_DIR / "episodes" / "1001-1100" / "ep.1001.md",
            IMAGE_PATH,
            IMAGE_DIR / "998.png",
            HTML_PATH,
            html_episode_path(BASE_DIR, "ep.999"),
            html_episode_path(BASE_DIR, "ep.1000"),
            html_episode_path(BASE_DIR, "ep.1001"),
        ):
            if path.exists():
                path.unlink()

        for directory in (
            HTML_PATH.parent,
            BASE_DIR / "html" / "1001-1100",
            EPISODE_PATH.parent,
            BASE_DIR / "episodes" / "1001-1100",
            IMAGE_DIR,
        ):
            if directory.exists() and not any(directory.iterdir()):
                directory.rmdir()

    def test_adult_episode_with_prelude_image_renders_html_illustration(self):
        IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        EPISODE_PATH.parent.mkdir(parents=True, exist_ok=True)
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
        shutil.copyfile(BASE_DIR / "images" / "characters" / "박미현.png", IMAGE_PATH)

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
        self.assertIn("../../images/preludes/901-1000/ep.998.png", html)
        self.assertIn("<figcaption>테스트 공간</figcaption>", html)
        self.assertNotIn("## [성인씬 #1 — ep.998]", html)
        self.assertNotIn("다시 만나는 관계들", html)

    def test_adult_episode_title_uses_markdown_heading_without_internal_suffix(self):
        EPISODE_PATH.parent.mkdir(parents=True, exist_ok=True)
        EPISODE_PATH.write_text(
            "\n".join(
                [
                    "# ep.998_a - 테스트 부제목",
                    "",
                    "샘플 본문.",
                ]
            ),
            encoding="utf-8",
        )

        result = subprocess.run(
            ["python3", "convert_html.py", "ep.998_a"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        html = HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("<title>ep.998 - 테스트 부제목</title>", html)
        self.assertIn("<h1>ep.998 - 테스트 부제목</h1>", html)
        self.assertNotIn("<h1>ep.998_a", html)

    def test_numeric_only_image_name_is_supported(self):
        IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        EPISODE_PATH.parent.mkdir(parents=True, exist_ok=True)
        EPISODE_PATH.write_text(
            "\n".join(
                [
                    "샘플 본문 첫 문장.",
                    "",
                    "---",
                    "## [성인씬 #1 — ep.998]",
                    "",
                    "- 장소: 숫자 파일명 테스트",
                    "- <progress>3단계</progress>",
                    "",
                    "---",
                    "",
                    "후속 문장.",
                ]
            ),
            encoding="utf-8",
        )
        numeric_image_path = IMAGE_DIR / "998.png"
        shutil.copyfile(BASE_DIR / "images" / "characters" / "박미현.png", numeric_image_path)

        result = subprocess.run(
            ["python3", "convert_html.py", "ep.998_a"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        html = HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("../../images/preludes/901-1000/998.png", html)
        self.assertIn("<figcaption>숫자 파일명 테스트</figcaption>", html)

    def test_unbracketed_adult_scene_heading_is_replaced_with_illustration(self):
        IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        EPISODE_PATH.parent.mkdir(parents=True, exist_ok=True)
        EPISODE_PATH.write_text(
            "\n".join(
                [
                    "도입 문장.",
                    "",
                    "---",
                    "## 성인씬 #1 — ep.998",
                    "",
                    "- 장소: 헤딩 변형 테스트",
                    "- <progress>3단계</progress>",
                    "",
                    "---",
                    "",
                    "후속 문장.",
                ]
            ),
            encoding="utf-8",
        )
        shutil.copyfile(BASE_DIR / "images" / "characters" / "박미현.png", IMAGE_PATH)

        result = subprocess.run(
            ["python3", "convert_html.py", "ep.998_a"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        html = HTML_PATH.read_text(encoding="utf-8")
        self.assertIn('class="scene-illustration"', html)
        self.assertIn("<figcaption>헤딩 변형 테스트</figcaption>", html)
        self.assertNotIn("## 성인씬 #1 — ep.998", html)

    def test_bracketed_adult_scene_with_blank_line_after_divider_is_replaced(self):
        IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        EPISODE_PATH.parent.mkdir(parents=True, exist_ok=True)
        EPISODE_PATH.write_text(
            "\n".join(
                [
                    "도입 문장.",
                    "",
                    "---",
                    "",
                    "## [성인씬 #1 — ep.998]",
                    "",
                    "- 장소: 빈 줄 포함 테스트",
                    "- <progress>2단계</progress>",
                    "",
                    "---",
                    "",
                    "후속 문장.",
                ]
            ),
            encoding="utf-8",
        )
        shutil.copyfile(BASE_DIR / "images" / "characters" / "박미현.png", IMAGE_PATH)

        result = subprocess.run(
            ["python3", "convert_html.py", "ep.998_a"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        html = HTML_PATH.read_text(encoding="utf-8")
        self.assertIn('class="scene-illustration"', html)
        self.assertIn("<figcaption>빈 줄 포함 테스트</figcaption>", html)
        self.assertNotIn("## [성인씬 #1 — ep.998]", html)

    def test_navigation_crosses_batch_folders_without_broken_links(self):
        prev_path = BASE_DIR / "episodes" / "901-1000" / "ep.999.md"
        boundary_path = BASE_DIR / "episodes" / "901-1000" / "ep.1000.md"
        next_path = BASE_DIR / "episodes" / "1001-1100" / "ep.1001.md"
        prev_path.parent.mkdir(parents=True, exist_ok=True)
        boundary_path.parent.mkdir(parents=True, exist_ok=True)
        next_path.parent.mkdir(parents=True, exist_ok=True)
        prev_path.write_text("999화", encoding="utf-8")
        boundary_path.write_text("1000화", encoding="utf-8")
        next_path.write_text("1001화", encoding="utf-8")
        EPISODE_PATH.parent.mkdir(parents=True, exist_ok=True)
        EPISODE_PATH.write_text("998화", encoding="utf-8")

        result = subprocess.run(
            ["python3", "convert_html.py", "ep.998_a", "ep.999", "ep.1000", "ep.1001"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        html_999 = html_episode_path(BASE_DIR, "ep.999").read_text(encoding="utf-8")
        html_1000 = html_episode_path(BASE_DIR, "ep.1000").read_text(encoding="utf-8")
        html_1001 = html_episode_path(BASE_DIR, "ep.1001").read_text(encoding="utf-8")
        self.assertIn('href="ep.998_a.html"', html_999)
        self.assertIn('href="ep.1000.html"', html_999)
        self.assertIn('href="../1001-1100/ep.1001.html"', html_1000)
        self.assertIn('href="../901-1000/ep.1000.html"', html_1001)


if __name__ == "__main__":
    unittest.main()
