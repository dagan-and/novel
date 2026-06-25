import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "generate.py"
SPEC = importlib.util.spec_from_file_location("baekje_generate", MODULE_PATH)
generate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generate)


class LoadTurnsTests(unittest.TestCase):
    def test_load_turns_reads_compact_turn_data(self):
        sample = [
            {
                "turn": 1,
                "year": "기원후 12년",
                "codename": "정리",
                "headline": "시험",
                "summary": "요약",
                "actions": [],
                "outcome": "결과",
                "state_changes": [],
                "risks": [],
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "turns.json"
            path.write_text(json.dumps(sample, ensure_ascii=False), encoding="utf-8")

            turns = generate.load_turns(path)

        self.assertEqual(turns[0]["codename"], "정리")

    def test_real_turn_data_contains_multiple_turns(self):
        turns = generate.load_turns(generate.BASE / "turns.json")

        self.assertGreaterEqual(len(turns), 10)


class HtmlRenderTests(unittest.TestCase):
    def test_generate_html_renders_korean_turn_navigation(self):
        turns = [
            {
                "turn": 1,
                "year": "기원후 12년",
                "codename": "정리",
                "headline": "백제가 숨을 고른다",
                "summary": "전황 브리핑",
                "actions": ["창고 재조사"],
                "outcome": "군량 회복",
                "state_changes": ["보급 안정"],
                "risks": ["귀족 반발"],
            }
        ]

        html = generate.generate_html(turns)

        self.assertIn("전황 브리핑", html)
        self.assertIn("다음 턴", html)
        self.assertIn("백제가 숨을 고른다", html)

    def test_write_html_creates_a_turn_by_turn_chronicle_file(self):
        turns = [
            {
                "turn": 1,
                "year": "기원후 12년",
                "codename": "정리",
                "headline": "시험",
                "summary": "요약",
                "actions": [],
                "outcome": "결과",
                "state_changes": [],
                "risks": [],
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "chronicle.html"

            generate.write_html(turns, target)

            self.assertTrue(target.exists())
            self.assertIn("이전 턴", target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
