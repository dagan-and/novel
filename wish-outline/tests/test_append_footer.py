import importlib.util
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
SCRIPT_PATH = TOOLS_DIR / "append_footer.py"
KEYWORDS_PATH = TOOLS_DIR / "footer_keywords.json"


def load_module():
    spec = importlib.util.spec_from_file_location("append_footer", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def minimal_pool():
    return {
        "categories": {
            "전조빌드업": ["전조"],
            "체위기동": ["전환"],
            "질자궁": ["핵심"],
            "구강인후": [],
            "목호흡": [],
            "신체반응": ["반응"],
            "시선": ["시선"],
            "청각세분": ["소리"],
            "템포리듬": ["템포"],
            "경계선": ["경계"],
            "정신파멸": ["심리"],
            "굴욕수치": ["수치"],
            "감각전환": ["감각"],
            "사후여파": ["여파"],
            "시간지속": ["시간"],
            "체액배설": ["체액"],
            "피스톤단계": ["단계"],
            "피스톤디테일": ["디테일"],
            "절정지연": ["지연"],
        },
        "character_traits": {"김민정": ["민정 특성"]},
        "closing_lines": ["마무리"],
    }


class AppendOutlineFooterTests(unittest.TestCase):
    def test_loads_keyword_pool_from_json_file(self):
        module = load_module()

        pool = module.load_keyword_pool(KEYWORDS_PATH)

        self.assertIn("categories", pool)
        self.assertIn("closing_lines", pool)

    def test_builds_footer_block_from_keyword_pool(self):
        module = load_module()

        footer = module.build_footer_text(minimal_pool(), "김민정", random.Random(1))

        self.assertIn("**********", footer)
        self.assertIn("[전조]", footer)
        self.assertIn("[캐릭터 특성 - 김민정]", footer)
        self.assertIn("마무리", footer)

    def test_appends_random_footer_once_even_when_run_twice(self):
        module = load_module()
        pool = minimal_pool()
        with tempfile.TemporaryDirectory() as temp_dir:
            outline = Path(temp_dir) / "sample.txt"
            outline.write_text("[성인씬 개요]\n\n도입:\n- 김민정 시작\n", encoding="utf-8")

            first = module.append_footer(outline, pool, random.Random(1))
            second = module.append_footer(outline, pool, random.Random(2))

            content = outline.read_text(encoding="utf-8")
            self.assertTrue(first.changed)
            self.assertFalse(second.changed)
            self.assertEqual(content.count("**********"), 1)
            self.assertEqual(content.count("<!-- outline-footer:"), 1)

    def test_applies_to_text_files_only(self):
        module = load_module()
        pool = minimal_pool()
        with tempfile.TemporaryDirectory() as temp_dir:
            outline_dir = Path(temp_dir)
            (outline_dir / "a.txt").write_text("a\n", encoding="utf-8")
            (outline_dir / "b.log").write_text("b\n", encoding="utf-8")
            (outline_dir / ".DS_Store").write_bytes(b"ignored")

            result = module.append_to_outline_dir(outline_dir, pool, random.Random(1))

            self.assertEqual(result.changed_count, 1)
            self.assertIn("**********", (outline_dir / "a.txt").read_text(encoding="utf-8"))
            self.assertNotIn("**********", (outline_dir / "b.log").read_text(encoding="utf-8"))
            self.assertEqual((outline_dir / ".DS_Store").read_bytes(), b"ignored")

    def test_cli_appends_footer_using_default_keyword_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            outline_dir = Path(temp_dir) / "outlines"
            outline_dir.mkdir()
            outline = outline_dir / "sample.txt"
            outline.write_text("원문\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--outline-dir",
                    str(outline_dir),
                    "--keywords-json",
                    str(KEYWORDS_PATH),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0)
            self.assertEqual(outline.read_text(encoding="utf-8").count("**********"), 1)


if __name__ == "__main__":
    unittest.main()
