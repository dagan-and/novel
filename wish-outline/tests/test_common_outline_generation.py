import json
import random
import tempfile
from dataclasses import replace
import unittest
from pathlib import Path
from unittest.mock import patch

import generate_outlines
import profiles


class ChoiceRecorder(random.Random):
    def __init__(self, selected_scene_type):
        super().__init__(0)
        self.selected_scene_type = selected_scene_type
        self.weight_call = None

    def choices(self, population, weights=None, *, cum_weights=None, k=1):
        self.weight_call = (list(population), list(weights), k)
        return [self.selected_scene_type]


class SingleReadPath:
    def __init__(self, contents):
        self.contents = contents
        self.reads = 0

    def read_text(self, encoding):
        self.reads += 1
        if self.reads > 1:
            raise AssertionError("common configuration was loaded more than once")
        return self.contents


class CommonOutlineGenerationTests(unittest.TestCase):
    def test_github_image_link_uses_raw_file_url(self):
        image_path = (
            generate_outlines.REPO_ROOT
            / "characters"
            / "이주은"
            / "image (1).png"
        )

        def fake_git_output(args, repo_root=generate_outlines.REPO_ROOT):
            if args == ["config", "--get", "remote.origin.url"]:
                return "git@github.com:dagan-and/novel.git"
            if args == ["branch", "--show-current"]:
                return "main"
            if args == ["rev-parse", "--show-toplevel"]:
                return str(generate_outlines.REPO_ROOT.parent)
            if args[:4] == ["-c", "core.quotePath=false", "ls-files", "--full-name"]:
                return ""
            raise AssertionError(args)

        with patch.object(generate_outlines, "git_output", fake_git_output):
            link = generate_outlines.github_image_link(image_path)

        self.assertEqual(
            link,
            "https://raw.githubusercontent.com/dagan-and/novel/main/wish-outline/characters/%EC%9D%B4%EC%A3%BC%EC%9D%80/image%20%281%29.png",
        )

    def test_github_image_link_uses_git_tracked_unicode_path(self):
        image_path = (
            generate_outlines.REPO_ROOT
            / "characters"
            / "이주은"
            / "1744440997553344.webp"
        )

        def fake_git_output(args, repo_root=generate_outlines.REPO_ROOT):
            if args == ["config", "--get", "remote.origin.url"]:
                return "git@github.com:dagan-and/novel.git"
            if args == ["branch", "--show-current"]:
                return "main"
            if args == ["rev-parse", "--show-toplevel"]:
                return str(generate_outlines.REPO_ROOT.parent)
            if args[:4] == ["-c", "core.quotePath=false", "ls-files", "--full-name"]:
                return "wish-outline/characters/이주은/1744440997553344.webp"
            raise AssertionError(args)

        with patch.object(generate_outlines, "git_output", fake_git_output):
            link = generate_outlines.github_image_link(image_path)

        self.assertEqual(
            link,
            "https://raw.githubusercontent.com/dagan-and/novel/main/wish-outline/characters/%EC%9D%B4%EC%A3%BC%EC%9D%80/1744440997553344.webp",
        )

    def test_load_characters_reads_profiles_inside_character_folders(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            character_dir = Path(temp_dir) / "characters"
            profile_dir = character_dir / "이주은"
            profile_dir.mkdir(parents=True)
            (profile_dir / "이주은.txt").write_text(
                "# 이주은\n\n"
                "## 기본 정보\n\n"
                "- 리부트 포지션: 치어리더\n"
                "- 체형: 슬림글래머\n\n"
                "## 말투\n\n차분하게 말한다.\n\n"
                "## 성격\n\n도도하다.\n\n"
                "## 외형\n\n긴 흑발이 돋보인다.\n",
                encoding="utf-8",
            )

            with patch.object(generate_outlines, "CHARACTER_DIR", character_dir):
                characters = generate_outlines.load_characters()

        self.assertEqual([character.name for character in characters], ["이주은"])
        self.assertEqual(characters[0].body_type, "슬림글래머")

    def test_image_generation_prompt_is_single_line_gpt_generation_request(self):
        char = generate_outlines.Character(
            name="이주은",
            profile="# 이주은",
            position="치어리더",
            body_type="슬림글래머",
            speech="차분하게 말한다.",
            personality="도도하다.",
            appearance="긴 흑발이 돋보인다.",
            points="치어 퍼포먼스",
            image_links=[
                "https://raw.githubusercontent.com/dagan-and/novel/main/wish-outline/characters/%EC%9D%B4%EC%A3%BC%EC%9D%80/image%20%281%29.png",
                "https://raw.githubusercontent.com/dagan-and/novel/main/wish-outline/characters/%EC%9D%B4%EC%A3%BC%EC%9D%80/1744440997553344.webp",
            ],
        )
        scene = {
            "place": "비상계단",
            "weather": "냉방 소리가 멀어진 늦은 밤",
            "pressure": "둘의 동선을 고립시킨다",
            "place_details": [],
            "clothes": "팀 유니폼과 플리츠 스커트",
            "hair": "고유 헤어스타일을 유지한다",
            "start": "둘만 남는다.",
            "turn": "관계가 전환된다.",
            "after": "감정이 남는다.",
        }

        prompt = generate_outlines.image_generation_prompt(char, scene)

        self.assertNotIn("\n", prompt)
        self.assertTrue(prompt.startswith("GPT 이미지 생성 요청입니다."))
        self.assertIn("분석하거나 설명하지 말고 반드시 새 이미지를 생성해줘", prompt)
        self.assertIn(
            "참조 이미지 URL은 자동화 코드가 GPT 이미지 입력으로 함께 전달해야 한다",
            prompt,
        )
        self.assertIn(
            "외형 참조 URL: https://raw.githubusercontent.com/dagan-and/novel/main/wish-outline/characters/%EC%9D%B4%EC%A3%BC%EC%9D%80/image%20%281%29.png, https://raw.githubusercontent.com/dagan-and/novel/main/wish-outline/characters/%EC%9D%B4%EC%A3%BC%EC%9D%80/1744440997553344.webp",
            prompt,
        )
        self.assertLess(prompt.index("외형 참조 URL:"), prompt.index("2026년 여름"))

    def test_outline_uses_single_line_image_generation_prompt(self):
        char = generate_outlines.Character(
            name="이주은",
            profile="# 이주은",
            position="치어리더",
            body_type="슬림글래머",
            speech="차분하게 말한다.",
            personality="도도하다.",
            appearance="긴 흑발이 돋보인다.",
            points="치어 퍼포먼스",
            image_links=[],
        )
        scene = {
            "place": "비상계단",
            "weather": "냉방 소리가 멀어진 늦은 밤",
            "pressure": "둘의 동선을 고립시킨다",
            "place_details": [],
            "clothes": "팀 유니폼과 플리츠 스커트",
            "hair": "고유 헤어스타일을 유지한다",
            "start": "둘만 남는다.",
            "turn": "관계가 전환된다.",
            "after": "감정이 남는다.",
        }

        outline = generate_outlines.outline_text(1, char, scene)
        prompt_block = outline.split("이미지 프롬프트:\n", 1)[1].split(
            "\n\n\n\n인물:",
            1,
        )[0]

        self.assertEqual(prompt_block, generate_outlines.image_generation_prompt(char, scene))

    def test_image_generation_prompt_preserves_reference_face_proportions(self):
        char = generate_outlines.Character(
            name="이주은",
            profile="# 이주은",
            position="치어리더",
            body_type="슬림글래머",
            speech="차분하게 말한다.",
            personality="도도하다.",
            appearance="긴 흑발이 돋보인다.",
            points="치어 퍼포먼스",
            image_links=[],
        )
        scene = {
            "place": "호텔 침실",
            "weather": "새벽 공기가 서늘하게 가라앉은 밤",
            "pressure": "둘의 동선을 고립시킨다",
            "place_details": [],
            "clothes": "불투명한 민소매 톱과 캐주얼한 호텔 룸웨어",
            "hair": "고유 헤어스타일을 유지한다",
            "start": "둘만 남는다.",
            "turn": "관계가 전환된다.",
            "after": "감정이 남는다.",
        }

        prompt = generate_outlines.image_generation_prompt(char, scene)

        self.assertIn("참조 이미지의 얼굴 비율을 최우선으로 유지한다", prompt)
        self.assertIn("눈을 크게 만들거나 또렷하게 확대 보정하지 않는다", prompt)
        self.assertIn("턱과 하관을 더 가늘거나 뾰족한 V라인으로 보정하지 않는다", prompt)
        self.assertIn("피부를 뷰티 필터처럼 매끈하게 만들지 않는다", prompt)
        self.assertIn("입만 웃는 표정이 아니라 입꼬리, 볼, 눈 주변이 함께 움직이는 자연스러운 미소", prompt)
        self.assertIn("잔머리와 앞머리는 계산된 뷰티 이미지처럼 정리하지 않는다", prompt)
        self.assertNotIn("beautiful Korean woman", prompt)
        self.assertNotIn("delicate youthful features", prompt)
        self.assertNotIn("small defined face", prompt)

    def test_outline_image_prompt_uses_natural_place_and_name_particles(self):
        char = generate_outlines.Character(
            name="박다정",
            profile="# 박다정",
            position="약사",
            body_type="육감",
            speech="필요한 말만 한다.",
            personality="침착하다.",
            appearance="차가운 인상이다.",
            points="약국 마감",
            image_links=[],
        )
        scene = {
            "place": "비상계단",
            "weather": "냉방 소리가 멀어진 늦은 밤",
            "pressure": "둘의 동선을 고립시킨다",
            "place_details": ["회색 방화문"],
            "clothes": "셔링 블라우스와 세미와이드 슬랙스",
            "hair": "고유 헤어스타일을 유지한다",
            "start": "둘만 남는다.",
            "turn": "관계가 전환된다.",
            "after": "감정이 남는다.",
        }

        outline = generate_outlines.outline_text(1, char, scene)

        self.assertIn("비상계단에서", outline)
        self.assertIn("성인 여성 박다정 한 명만", outline)
        self.assertIn("비상계단의 공간감", outline)
        self.assertNotIn("비상계단을에서", outline)
        self.assertNotIn("박다정은 한 명", outline)

    def test_outline_preserves_full_profile_line_breaks(self):
        char = generate_outlines.Character(
            name="박다정",
            profile="# 박다정\n\n## 기본 정보\n\n- 체형: 육감\n\n## 말투\n\n차분하게 말한다.",
            position="약사",
            body_type="육감",
            speech="필요한 말만 한다.",
            personality="침착하다.",
            appearance="차가운 인상이다.",
            points="약국 마감",
            image_links=[],
        )
        scene = {
            "place": "비상계단",
            "weather": "냉방 소리가 멀어진 늦은 밤",
            "pressure": "둘의 동선을 고립시킨다",
            "place_details": [],
            "clothes": "셔링 블라우스와 세미와이드 슬랙스",
            "hair": "고유 헤어스타일을 유지한다",
            "start": "둘만 남는다.",
            "turn": "관계가 전환된다.",
            "after": "감정이 남는다.",
        }

        outline = generate_outlines.outline_text(1, char, scene)
        profile_block = outline.split("여성 캐릭터 전체 프로필:\n\n", 1)[1].split(
            "\n\n시기:",
            1,
        )[0]

        self.assertEqual(
            profile_block,
            "# 박다정\n\n## 기본 정보\n\n- 체형: 육감\n\n## 말투\n\n차분하게 말한다.",
        )

    def test_load_characters_reads_body_type_without_json_profiles(self):
        characters = generate_outlines.load_characters()
        self.assertTrue(characters)
        self.assertTrue(all(character.body_type for character in characters))

    def test_all_text_characters_are_selectable(self):
        characters = generate_outlines.load_characters()
        selected = generate_outlines.selectable_characters(characters)
        self.assertEqual([char.name for char in selected], [char.name for char in characters])

    def test_named_text_character_can_be_selected(self):
        characters = generate_outlines.load_characters()
        character_name = characters[0].name
        selected = generate_outlines.selectable_characters(characters, character_name)
        self.assertEqual([char.name for char in selected], [character_name])

    def test_select_scene_uses_work_60_indoor_40(self):
        char = generate_outlines.load_characters()[0]
        rng = ChoiceRecorder("work")
        config = generate_outlines.get_common_scene_config()

        scene = generate_outlines.select_scene(1, char, rng)

        self.assertEqual(rng.weight_call, (["work", "indoor"], [60, 40], 1))
        self.assertEqual(scene["scene_type"], "work")
        self.assertIn(
            scene["place"],
            {location["place"] for location in config["locations"]["work"]},
        )

    def test_select_scene_uses_matching_body_type_outfit(self):
        char = generate_outlines.load_characters()[0]
        config = generate_outlines.get_common_scene_config()

        scene = generate_outlines.select_scene(1, char, ChoiceRecorder("indoor"))

        self.assertIn(scene["clothes"], config["outfits"][char.body_type]["indoor"])
        self.assertEqual(scene["hair"], "캐릭터 프로필에 명시된 고유 헤어스타일을 유지한다")

    def test_select_scene_rejects_unsupported_body_type(self):
        char = generate_outlines.load_characters()[0]
        unsupported = replace(char, body_type="알수없음")

        with self.assertRaisesRegex(ValueError, "unsupported character body type"):
            generate_outlines.select_scene(1, unsupported, ChoiceRecorder("work"))

    def test_select_scene_uses_arcs_from_its_validated_config(self):
        char = generate_outlines.load_characters()[0]
        payload = json.loads(profiles.COMMON_ARCS_PATH.read_text(encoding="utf-8"))
        payload["arcs"] = [
            {"type": "first", "start": "s1", "turn": "t1", "after": "a1"},
            {"type": "second", "start": "s2", "turn": "t2", "after": "a2"},
        ]
        common_config = json.dumps(payload)
        single_read_path = SingleReadPath(common_config)
        character_index = generate_outlines.character_names().index(char.name)
        expected_arc = generate_outlines.pick(
            payload["arcs"],
            1,
            character_index + 7,
        )

        with patch.object(profiles, "COMMON_ARCS_PATH", single_read_path):
            scene = generate_outlines.select_scene(1, char, ChoiceRecorder("work"))

        self.assertEqual(scene["arc_type"], expected_arc["type"])

    def test_select_scene_uses_location_fallback_without_arcs(self):
        char = generate_outlines.load_characters()[0]
        config = profiles.get_common_scene_config()
        config["arcs"] = []

        with patch.object(
            generate_outlines,
            "get_common_scene_config",
            return_value=config,
        ):
            scene = generate_outlines.select_scene(1, char, ChoiceRecorder("work"))

        self.assertEqual(scene["arc_type"], "location_driven")
        self.assertIn(scene["place"], scene["start"])
        self.assertIn(char.name, scene["turn"])
        self.assertTrue(scene["after"])

    def test_generate_outlines_rejects_invalid_body_type_before_creating_output_dir(self):
        character = generate_outlines.load_characters()[0]
        unsupported = replace(character, body_type="알수없음")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "outlines"
            with patch.object(
                generate_outlines,
                "load_characters",
                return_value=[unsupported],
            ):
                with self.assertRaisesRegex(ValueError, "unsupported character body type"):
                    generate_outlines.generate_outlines(1, output_dir=output_dir)

            self.assertFalse(output_dir.exists())

    def test_generate_outlines_writes_without_character_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            written = generate_outlines.generate_outlines(
                2,
                output_dir=Path(temp_dir),
                rng=random.Random(7),
            )

            self.assertEqual([path.name for path in written], ["001화.txt", "002화.txt"])
            self.assertTrue(
                all("이번 씬 복장:" in path.read_text(encoding="utf-8") for path in written)
            )

    def test_seeded_generation_is_byte_identical_in_separate_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            first_dir = Path(temp_dir) / "first"
            second_dir = Path(temp_dir) / "second"
            first = generate_outlines.generate_outlines(
                4,
                output_dir=first_dir,
                rng=random.Random(91),
            )
            second = generate_outlines.generate_outlines(
                4,
                output_dir=second_dir,
                rng=random.Random(91),
            )

            self.assertEqual([path.name for path in first], [path.name for path in second])
            self.assertEqual(
                [path.read_bytes() for path in first],
                [path.read_bytes() for path in second],
            )
