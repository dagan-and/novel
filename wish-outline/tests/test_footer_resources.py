import tempfile
import unittest
import json
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
                "정신파멸",
                "질자궁",
                "체위기동",
                "피스톤단계",
            },
        )

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
            self.assertIn("[1라운드]", updated)
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
