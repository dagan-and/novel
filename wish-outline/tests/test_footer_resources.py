import tempfile
import unittest
import json
import random
from pathlib import Path

from tools import append_footer


class FooterResourceTests(unittest.TestCase):
    def test_common_keyword_categories_only_include_used_footer_inputs(self):
        keywords_path = append_footer.PROJECT_ROOT / append_footer.KEYWORDS_JSON_DEFAULT
        data = json.loads(keywords_path.read_text(encoding="utf-8"))

        self.assertEqual(
            set(data["categories"]),
            {
                "구강인후",
                "굴욕수치",
                "목호흡",
                "신체반응",
                "전조빌드업",
                "질자궁",
                "체위기동",
                "피스톤단계",
            },
        )

    def test_character_traits_only_include_used_footer_inputs(self):
        character_path = append_footer.PROJECT_ROOT / append_footer.CHARACTER_JSON_DEFAULT
        data = json.loads(character_path.read_text(encoding="utf-8"))

        self.assertEqual(
            set(data),
            {
                "body_type_keywords",
                "body_type_outputs",
                "body_type_order",
                "personality_type_keywords",
                "body_type_instructions",
            },
        )

    def test_templates_only_include_used_footer_blocks(self):
        templates = append_footer.load_templates(
            append_footer.PROJECT_ROOT / append_footer.TEMPLATES_DEFAULT
        )

        self.assertEqual(
            set(templates),
            {
                "MALE_SPEC",
                "COMMON_INSTRUCTIONS",
                "ROUND_NOTE_LATE",
                "ROUND_NOTE_LAST",
            },
        )

    def test_footer_outputs_sentence_style_round_plan_with_custom_hooks(self):
        pool = {
            "categories": {
                "전조빌드업": ["도입A"],
                "체위기동": ["구도A", "구도B", "구도C"],
                "질자궁": ["핵심A"],
                "구강인후": ["핵심B"],
                "목호흡": [],
                "신체반응": ["반응A"],
                "굴욕수치": ["수치A"],
                "피스톤단계": ["단계A"],
            },
            "female_climax_sets": ["결과A"],
            "simultaneous_climax_sets": ["결과B"],
            "male_response": {"default": ["제압A"]},
            "female_resistance": {"default": ["저항A"]},
            "closing_lines": ["마무리A"],
        }
        templates = {
            "ROUND_NOTE_LATE": "###3구간 이상###",
            "ROUND_NOTE_LAST": "###마지막구간###",
        }

        footer = append_footer.build_footer_text(pool, templates, rng=random.Random(1))

        self.assertTrue(footer.startswith("**********\n라운드 "))
        self.assertIn("[순차 진행표]", footer)
        self.assertIn("[3구간:", footer)
        self.assertIn("###3구간 이상###", footer)
        self.assertIn("###마지막구간###", footer)
        self.assertEqual(footer.count("###3구간 이상###"), 1)
        self.assertEqual(footer.count("###마지막구간###"), 1)
        self.assertNotIn("[전조]", footer)
        self.assertNotIn("[1라운드]", footer)

    def test_footer_builds_round_plan_from_category_pools_without_structured_positions(self):
        pool = {
            "categories": {
                "전조빌드업": ["도입A"],
                "체위기동": ["구도A", "구도B", "구도C"],
                "질자궁": ["핵심A"],
                "구강인후": ["핵심B"],
                "목호흡": [],
                "신체반응": ["반응A"],
                "굴욕수치": ["수치A"],
                "피스톤단계": ["단계A"],
            },
            "female_climax_sets": ["결과A"],
            "simultaneous_climax_sets": ["결과B"],
            "male_response": {"default": ["제압A"]},
            "female_resistance": {"default": ["저항A"]},
            "closing_lines": ["마무리A"],
        }

        footer = append_footer.build_footer_text(pool, {}, rng=random.Random(1))

        self.assertIn("[1구간:", footer)
        self.assertIn("구도", footer)
        self.assertIn("단계A", footer)
        self.assertIn("반응A", footer)

    def test_resistance_pairs_only_appear_in_odd_numbered_sections(self):
        pool = {
            "categories": {
                "전조빌드업": ["도입A"],
                "굴욕수치": ["수치A"],
            },
            "체위": [
                {"name": "구도1", "피스톤": ["단계A"], "코어자극": ["핵심A"], "신체반응": ["반응A"]},
            ],
            "저항제압": {
                "default": [
                    {"저항": "저항A", "제압": "제압A"},
                    {"저항": "저항B", "제압": "제압B"},
                    {"저항": "저항C", "제압": "제압C"},
                ],
            },
            "female_climax_sets": ["결과A"],
            "simultaneous_climax_sets": ["결과B"],
            "closing_lines": ["마무리A"],
        }

        footer = append_footer.build_footer_text(pool, {}, rng=random.Random(1))

        sections = footer.split("\n[순차 진행표]\n", 1)[1].split("\n========================================", 1)[0]
        for round_num in range(1, 5):
            section = sections.split(f"\n[{round_num}구간:", 1)[1].split(f"\n[{round_num + 1}구간:", 1)[0] if round_num < 4 else sections.split(f"\n[{round_num}구간:", 1)[1]
            if round_num in {1, 3}:
                self.assertIn("여성 저항은", section)
                self.assertIn("남성 제압 방식은", section)
            else:
                self.assertNotIn("여성 저항은", section)
                self.assertNotIn("남성 제압 방식은", section)

    def test_fifth_section_can_receive_resistance_pair(self):
        pool = {
            "categories": {
                "전조빌드업": ["도입A"],
                "굴욕수치": ["수치A"],
            },
            "체위": [
                {"name": "구도1", "피스톤": ["단계A"], "코어자극": ["핵심A"], "신체반응": ["반응A"]},
            ],
            "저항제압": {
                "default": [
                    {"저항": "저항A", "제압": "제압A"},
                    {"저항": "저항B", "제압": "제압B"},
                    {"저항": "저항C", "제압": "제압C"},
                ],
            },
            "female_climax_sets": ["결과A"],
            "simultaneous_climax_sets": ["결과B"],
            "closing_lines": ["마무리A"],
        }

        footer = append_footer.build_footer_text(pool, {}, rng=random.Random(0))
        sections = footer.split("\n[순차 진행표]\n", 1)[1].split("\n========================================", 1)[0]
        fifth_section = sections.split("\n[5구간:", 1)[1]

        self.assertIn("라운드 5번", footer)
        self.assertIn("여성 저항은", fifth_section)
        self.assertIn("남성 제압 방식은", fifth_section)

    def test_resistance_and_response_are_selected_from_same_pair(self):
        pool = {
            "categories": {
                "전조빌드업": ["도입A"],
                "굴욕수치": ["수치A"],
            },
            "체위": [
                {"name": "구도1", "피스톤": ["단계A"], "코어자극": ["핵심A"], "신체반응": ["반응A"]},
            ],
            "저항제압": {
                "default": [
                    {"저항": "저항A", "제압": "제압A"},
                    {"저항": "저항B", "제압": "제압B"},
                ],
            },
            "female_climax_sets": ["결과A"],
            "simultaneous_climax_sets": ["결과B"],
            "closing_lines": ["마무리A"],
        }

        footer = append_footer.build_footer_text(pool, {}, rng=random.Random(1))
        resistance_lines = [line for line in footer.splitlines() if "여성 저항은" in line]

        self.assertTrue(resistance_lines)
        for line in resistance_lines:
            self.assertTrue(
                ("저항A" in line and "제압A" in line)
                or ("저항B" in line and "제압B" in line)
            )

    def test_get_trait_key_maps_known_trait_markers(self):
        self.assertEqual(append_footer.get_trait_key("성향: 강함"), "aggressive")
        self.assertEqual(append_footer.get_trait_key("dominant"), "aggressive")
        self.assertEqual(append_footer.get_trait_key("성향: 순종"), "submissive")
        self.assertEqual(append_footer.get_trait_key("weak / 약함"), "submissive")
        self.assertEqual(append_footer.get_trait_key("성향: 보통"), "default")

    def test_female_climax_sets_use_detected_trait_pool(self):
        pool = {
            "categories": {
                "전조빌드업": ["도입A"],
                "굴욕수치": ["수치A"],
            },
            "체위": [
                {"name": "구도1", "피스톤": ["단계A"], "코어자극": ["핵심A"], "신체반응": ["반응A"]},
            ],
            "personality_type_keywords": {
                "강함": ["성향: 강함"],
                "여림": ["성향: 여림"],
            },
            "저항제압": {
                "aggressive": [{"저항": "저항A", "제압": "제압A"}],
                "default": [{"저항": "저항B", "제압": "제압B"}],
            },
            "female_climax_sets": {
                "aggressive": ["강함절정A"],
                "default": ["기본절정A"],
            },
            "simultaneous_climax_sets": ["첫결과A"],
            "mid_cum_sets": ["중간결과A"],
            "facial_cum_sets": ["굴욕결과A"],
            "closing_lines": ["마무리A"],
        }

        footer = append_footer.build_footer_text(
            pool,
            {},
            content="인물 프로필\n성향: 강함\n",
            rng=random.Random(0),
        )

        self.assertIn("세부 결과 메모: 강함절정A", footer)
        self.assertNotIn("세부 결과 메모: 기본절정A", footer)
        self.assertNotIn("세부 결과 메모: aggressive", footer)

    def test_round_result_label_supports_cum_stage_types(self):
        self.assertEqual(
            append_footer.round_result_label("첫질내사정"),
            "여성 절정 + 첫 질내 사정",
        )
        self.assertEqual(
            append_footer.round_result_label("중간질내사정"),
            "여성 절정 + 중간 질내 사정",
        )
        self.assertEqual(
            append_footer.round_result_label("굴욕사정"),
            "여성 절정 + 남성 굴욕 사정",
        )

    def test_shame_cum_set_is_always_assigned_to_last_round(self):
        pool = {
            "categories": {
                "전조빌드업": ["도입A"],
                "굴욕수치": ["수치A"],
            },
            "체위": [
                {"name": "구도1", "피스톤": ["단계A"], "코어자극": ["핵심A"], "신체반응": ["반응A"]},
            ],
            "female_climax_sets": ["여성결과A"],
            "simultaneous_climax_sets": ["첫결과A", "첫결과B"],
            "mid_cum_sets": ["중간결과A"],
            "facial_cum_sets": ["굴욕결과A"],
            "closing_lines": ["마무리A"],
        }

        footer = append_footer.build_footer_text(pool, {}, rng=random.Random(0))
        sections = footer.split("\n[순차 진행표]\n", 1)[1].split("\n========================================", 1)[0]
        last_section = sections.split("\n[5구간:", 1)[1]
        earlier_sections = sections.split("\n[5구간:", 1)[0]

        self.assertIn("라운드 5번", footer)
        self.assertIn("결과: 여성 절정 + 남성 굴욕 사정.", last_section)
        self.assertIn("세부 결과 메모: 굴욕결과A", last_section)
        self.assertNotIn("굴욕결과A", earlier_sections)
        self.assertNotIn("남성 굴욕 사정", earlier_sections)
        self.assertEqual(footer.count("결과: 여성 절정 + 첫 질내 사정."), 1)
        self.assertEqual(footer.count("결과: 여성 절정 + 중간 질내 사정."), 1)
        self.assertIn("중간결과A", earlier_sections)

    def test_shame_only_appears_in_last_round_and_mind_is_omitted(self):
        pool = {
            "categories": {
                "전조빌드업": ["도입A"],
                "체위기동": ["구도A", "구도B", "구도C", "구도D"],
                "질자궁": ["핵심A"],
                "구강인후": ["핵심B"],
                "목호흡": [],
                "신체반응": ["반응A"],
                "굴욕수치": ["수치A"],
                "피스톤단계": ["단계A"],
            },
            "female_climax_sets": ["결과A"],
            "simultaneous_climax_sets": ["결과B"],
            "male_response": {"default": ["제압A"]},
            "female_resistance": {"default": ["저항A"]},
            "closing_lines": ["마무리A"],
        }

        footer = append_footer.build_footer_text(pool, {}, rng=random.Random(1))

        self.assertEqual(footer.count("수치 요소는 수치A"), 1)
        self.assertNotIn("정신 변화", footer)

        last_round_index = footer.rindex("[4구간:")
        self.assertGreater(footer.index("수치 요소는 수치A"), last_round_index)

    def test_main_uses_all_default_footer_resources(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            outline_path = Path(temp_dir) / "001화.txt"
            outline_path.write_text(
                "인물 프로필\n- 체형: 슬림글래머\n- 성향: 강함\n",
                encoding="utf-8",
            )

            result = append_footer.main(["--outline-dir", temp_dir])

            self.assertEqual(result, 0)
            updated = outline_path.read_text(encoding="utf-8")
            footer = updated.split("<!-- outline-footer:", 1)[1]
            self.assertIn("체형: 마른 몸매 위로", footer)
            self.assertIn("성향: 강함", footer)
            self.assertIn("[체형별 지시]", updated)
            self.assertIn("[1구간:", updated)
            self.assertIn("남성 사정", updated)

    def test_body_type_detection_uses_canonical_key_but_outputs_description(self):
        pool = append_footer.load_footer_pool(
            append_footer.PROJECT_ROOT / append_footer.KEYWORDS_JSON_DEFAULT,
            append_footer.PROJECT_ROOT / append_footer.CHARACTER_JSON_DEFAULT,
        )
        templates = append_footer.load_templates(
            append_footer.PROJECT_ROOT / append_footer.TEMPLATES_DEFAULT
        )

        footer = append_footer.build_footer_text(
            pool,
            templates,
            "인물 프로필\n- 체형: 슬림글래머\n- 성향: 보통\n",
        )

        self.assertIn("체형: 마른 몸매 위로", footer)


if __name__ == "__main__":
    unittest.main()
