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
                "summary": ["요약 첫 문단", "요약 둘째 문단"],
                "actions": [],
                "outcome": "결과",
                "frontline": "전선은 아직 열리지 않았지만, 창고와 도로가 이미 다음 전쟁의 속도를 바꾸고 있었다.",
                "court_reaction": "귀족들은 불만을 삼켰고, 실무 관료들은 처음으로 왕권이 모든 창고를 본다는 사실을 실감했다.",
                "enemy_reaction": "주변 세력은 백제가 당장 치지 않는다는 점에서 오히려 더 큰 불안을 느꼈다.",
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
                "summary": ["전황 브리핑", "두 번째 문단"],
                "actions": ["창고 재조사"],
                "outcome": "군량 회복",
                "frontline": "병사들은 아직 출정하지 않았지만, 병참선은 이미 움직이기 시작했다.",
                "court_reaction": "궁정은 불만과 경외가 뒤섞인 채 천인의 명령을 따랐다.",
                "enemy_reaction": "적국은 백제가 칼보다 계산을 먼저 뽑아든 것을 두려워했다.",
                "state_changes": ["보급 안정"],
                "risks": ["귀족 반발"],
            }
        ]

        html = generate.generate_html(turns)

        self.assertIn("전황 브리핑", html)
        self.assertIn("다음 턴", html)
        self.assertIn("백제가 숨을 고른다", html)
        self.assertIn("전선 동향", html)
        self.assertIn("궁정 반응", html)
        self.assertIn("적국 반응", html)
        self.assertIn("두 번째 문단", html)

    def test_write_html_creates_a_turn_by_turn_chronicle_file(self):
        turns = [
            {
                "turn": 1,
                "year": "기원후 12년",
                "codename": "정리",
                "headline": "시험",
                "summary": ["요약 첫 문단", "요약 둘째 문단"],
                "actions": [],
                "outcome": "결과",
                "frontline": "전선 변화 없음",
                "court_reaction": "조정 소란",
                "enemy_reaction": "적국 정탐 강화",
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
