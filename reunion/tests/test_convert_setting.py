import subprocess
import unittest
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]


class ConvertSettingTitleTests(unittest.TestCase):
    def test_generated_setting_pages_omit_series_title(self):
        result = subprocess.run(
            ["python3", "convert_setting.py"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)

        index_html = (BASE_DIR / "html" / "index.html").read_text(encoding="utf-8")
        world_html = (BASE_DIR / "html" / "setting" / "세계관.html").read_text(encoding="utf-8")
        relation_html = (BASE_DIR / "html" / "setting" / "관계망.html").read_text(encoding="utf-8")
        timeline_html = (BASE_DIR / "html" / "setting" / "연대기.html").read_text(encoding="utf-8")

        self.assertNotIn("다시 만나는 관계들", index_html)
        self.assertNotIn("다시 만나는 관계들", world_html)
        self.assertNotIn("다시 만나는 관계들", relation_html)
        self.assertNotIn("다시 만나는 관계들", timeline_html)
        self.assertIn('href="preludes.html"', index_html)
        self.assertIn(">삽화<", index_html)
        self.assertIn("총 200화 완성", index_html)
        self.assertIn('href="001-100/ep.001.html"', index_html)
        self.assertIn('href="101-200/ep.200_a.html"', index_html)


if __name__ == "__main__":
    unittest.main()
