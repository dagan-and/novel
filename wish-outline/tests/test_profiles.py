from contextlib import redirect_stderr
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "generate_outlines.py"
KIM_JSON_PATH = REPO_ROOT / "profiles" / "김민정.json"

REQUESTED_PLACES = {
    "김민정": ["고급호텔 스위트룸", "고급호텔 실내 수영장", "고급호텔 라운지", "e스포츠 경기장 무대 뒤 통로", "심야 PC방 커플석", "중계 부스 옆 빈 관람석", "게임 행사장 물품 창고", "PC방 옥상", "뒤풀이 술집 구석자리", "무인 보드게임 카페"],
    "노은화": ["고급호텔 스위트룸", "고급호텔 실내 수영장", "고급호텔 바", "이자카야 뒷문 골목", "새벽 편의점 테이블", "비 오는 버스정류장", "무인 빨래방", "건물 옥상 난간", "칵테일 재료상 창고", "새벽 시장 골목"],
    "도하영": ["고급호텔 스위트룸", "고급호텔 실내 수영장", "고급호텔 예절 교육장", "항공서비스학과 실습실", "면접 연습용 거울 앞", "공항 라운지 실습 구역", "캐리어 보관소", "학교 옥상", "빈 강의동 계단참", "공항 전망대 구석"],
    "문아영": ["고급호텔 스위트룸", "고급호텔 실내 수영장", "고급호텔 갤러리 라운지", "미대 작업실 창가", "물감 묻은 세면대 앞", "캔버스 보관 창고", "독립 갤러리 뒷문", "졸업전시 설치장 구석", "학교 옥상", "한강 다리 밑 벽화길"],
    "박다정": ["고급호텔 스위트룸", "고급호텔 실내 수영장", "고급호텔 메디컬 라운지", "약국 마감 후 카운터", "조명 꺼진 약국 유리문 앞", "처방전 보관함 옆", "약국 뒤 창고", "병원 건물 비상계단", "심야 무인 카페", "흰 가운 걸린 휴게실"],
    "박미현": ["고급호텔 스위트룸", "고급호텔 실내 수영장", "고급호텔 디저트 라운지", "디저트 카페 창가 자리", "새벽 베이킹실", "제과 주방 뒷문", "케이크 쇼케이스 앞", "카페 창고", "비 오는 골목 벤치", "제과 재료상"],
    "박세연": ["고급호텔 스위트룸", "고급호텔 실내 수영장", "고급호텔 공연장 객석", "발레 연습실 거울 앞", "무대 뒤 좁은 복도", "빈 관객석", "극장 옆문 계단", "늦은 귀갓길 정류장", "스트레칭 매트 구석", "공연장 지하 통로"],
    "서나윤": ["고급호텔 스위트룸", "고급호텔 실내 수영장", "고급호텔 피트니스 센터", "필라테스 센터 거울벽 앞", "리포머 옆 좁은 통로", "센터 마감 후 복도", "샤워실 앞 대기공간", "운동 후 골목", "센터 옥상", "새벽 헬스장 스트레칭존"],
    "서지수": ["고급호텔 스위트룸", "고급호텔 실내 수영장", "고급호텔 라운지", "백화점 명품관 VIP 피팅룸", "폐점 후 백화점 복도", "조용한 바 카운터 끝자리", "프라이빗 쇼룸", "선물 포장실 앞", "고급 레스토랑 프라이빗룸", "심야 와인숍"],
    "오유림": ["고급호텔 스위트룸", "고급호텔 실내 수영장", "고급호텔 라운지 피아노 옆", "빈 피아노실", "음대 연습실 복도", "소극장 객석 맨 뒤", "악보 보관실", "콩쿠르 리허설장 구석", "학교 음악관 옥상", "조용한 LP 카페"],
    "유하린": ["고급호텔 스위트룸", "고급호텔 실내 수영장", "고급호텔 스파 라운지", "피부과 상담실", "병원 마감 후 데스크", "아파트 공동현관", "비 오는 엘리베이터 앞", "아파트 계단참", "장 보고 돌아오는 골목", "아파트 옥상 정원"],
    "이주은": ["고급호텔 스위트룸", "고급호텔 실내 수영장", "고급호텔 비즈니스 라운지", "야근 후 사무실", "복사실", "임원실 앞 복도", "퇴근 엘리베이터", "사옥 비상계단", "자료실", "회사 지하 주차장"],
    "이주희": ["고급호텔 스위트룸", "고급호텔 실내 수영장", "고급호텔 조식 라운지", "캠퍼스 카페 창가", "유치원 행사 뒤 빈 교실", "공원 벤치", "동네 백반집 구석", "산책길 가로등 아래", "학교 도서관 뒤뜰", "놀이터 옆 벤치"],
    "이채영": ["고급호텔 스위트룸", "고급호텔 실내 수영장", "고급호텔 피팅 살롱", "아파트 엘리베이터", "공동현관 택배함 앞", "늦은 밤 분리수거장", "촬영 스튜디오 피팅룸", "샘플 의상 창고", "아파트 비상계단", "무인 카페"],
    "이하은": ["고급호텔 스위트룸", "고급호텔 실내 수영장", "고급호텔 프라이빗 레슨룸", "빈 발레 스튜디오", "거울벽 앞 바", "스트레칭 매트 구석", "비 오는 출구", "토슈즈 보관함 앞", "무용학원 옥상", "작은 공연장 객석"],
    "임세라": ["고급호텔 스위트룸", "고급호텔 실내 수영장", "고급호텔 행사장 연결 복도", "패션 쇼룸 테라스", "브랜드 행사장 백스테이지", "피팅룸 앞 복도", "협찬 미팅룸", "행사 뒤풀이 바", "샘플 의상 창고", "편집숍 폐점 후 매장"],
    "차소연": ["고급호텔 스위트룸", "고급호텔 실내 수영장", "고급호텔 로비 구석 소파", "리셉션 데스크 뒤편", "짐 보관실", "호텔 엘리베이터", "늦은 체크인 카운터", "레스토랑 예약 데스크", "직원 전용 복도", "객실 카드키 보관함 앞"],
    "최유진": ["고급호텔 스위트룸", "고급호텔 실내 수영장", "고급호텔 포토존 라운지", "사진 스튜디오 조명 뒤", "보정 노트북 앞", "옥상 자연광 촬영장", "늦은 밤 인화소", "미대 과제실", "스튜디오 장비 창고", "포토부스 커튼 안"],
    "최윤서": ["고급호텔 스위트룸", "고급호텔 실내 수영장", "고급호텔 라운지 창가", "공항 라운지 창가", "호텔 셔틀버스 뒷자리", "캐리어 보관소 앞", "공항 전망대", "비행 후 막차 정류장", "라운지 직원 통로", "조용한 공항 카페"],
    "한서진": ["고급호텔 스위트룸", "고급호텔 실내 수영장", "고급호텔 라운지 창가석", "객실 층 복도", "VIP 엘리베이터", "프론트 뒤 사무공간", "룸서비스 준비실", "호텔 바 가장 안쪽 좌석", "직원 전용 휴게실", "카드키 보관함 앞"],
}


def load_generator():
    spec = importlib.util.spec_from_file_location("generate_outlines", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CharacterProfileTests(unittest.TestCase):
    def test_all_character_profiles_match_the_requested_contract(self):
        required_event_keys = {
            "id", "place", "weather", "pressure", "place_details",
            "exposure_focus", "outfit_pool", "hair_pool",
        }
        all_outfits = []
        all_hairs = []

        for name, places in REQUESTED_PLACES.items():
            with self.subTest(character=name):
                profile_path = REPO_ROOT / "profiles" / f"{name}.json"
                self.assertTrue(profile_path.exists(), f"missing profile: {name}")
                import json

                profile = json.loads(profile_path.read_text(encoding="utf-8"))
                self.assertEqual(profile["name"], name)
                self.assertEqual([event["place"] for event in profile["events"]], places)
                self.assertEqual(len(profile["events"]), 10)

                for event in profile["events"]:
                    self.assertEqual(set(event), required_event_keys)
                    self.assertEqual(len(event["outfit_pool"]), 10)
                    self.assertEqual(len(set(event["outfit_pool"])), 10)
                    self.assertEqual(len(event["hair_pool"]), 5)
                    self.assertEqual(len(set(event["hair_pool"])), 5)
                    self.assertTrue(all(isinstance(value, str) and value.strip() for value in event["outfit_pool"]))
                    self.assertTrue(all(isinstance(value, str) and value.strip() for value in event["hair_pool"]))
                    self.assertIsInstance(event["place_details"], list)
                    self.assertTrue(event["place_details"])
                    self.assertNotIn("arcs", event)
                    self.assertNotIn("place_rules", event)
                    all_outfits.extend(event["outfit_pool"])
                    all_hairs.extend(event["hair_pool"])

        self.assertEqual(len(all_outfits), len(set(all_outfits)))
        self.assertEqual(len(all_hairs), len(set(all_hairs)))

    def test_select_scene_supports_every_profiled_character(self):
        module = load_generator()
        characters = {character.name: character for character in module.load_characters()}

        for name in REQUESTED_PLACES:
            with self.subTest(character=name):
                scene = module.select_scene(1, characters[name])
                self.assertEqual(scene["profile_name"], name)
                self.assertIn(scene["place"], REQUESTED_PLACES[name])

    def test_get_common_arcs_loads_non_empty_validated_arcs(self):
        import profiles

        self.assertTrue(
            hasattr(profiles, "get_common_arcs"),
            "profiles must expose get_common_arcs",
        )
        arcs = profiles.get_common_arcs()

        self.assertGreaterEqual(len(arcs), 1)
        for arc in arcs:
            self.assertEqual(set(arc), {"type", "start", "turn", "after"})
            for key in ("type", "start", "turn", "after"):
                self.assertIsInstance(arc[key], str)
                self.assertTrue(arc[key].strip())

    def test_get_common_arcs_rejects_missing_file(self):
        import profiles

        with tempfile.TemporaryDirectory() as temporary_directory:
            missing_path = Path(temporary_directory) / "missing.json"
            with patch.object(profiles, "COMMON_ARCS_PATH", missing_path):
                with self.assertRaisesRegex(ValueError, "common arcs"):
                    profiles.get_common_arcs()

    def test_get_common_arcs_rejects_empty_or_malformed_entries(self):
        import profiles

        invalid_payloads = [
            '{"arcs": []}',
            '{"arcs": [{"type": "male_b", "start": "", "turn": "말", "after": "말"}]}',
            '{"arcs": [{"type": "male_b", "start": "말", "turn": "말"}]}',
        ]

        with tempfile.TemporaryDirectory() as temporary_directory:
            common_arcs_path = Path(temporary_directory) / "common_arcs.json"
            with patch.object(profiles, "COMMON_ARCS_PATH", common_arcs_path):
                for payload in invalid_payloads:
                    with self.subTest(payload=payload):
                        common_arcs_path.write_text(payload, encoding="utf-8")
                        with self.assertRaisesRegex(ValueError, "common arcs"):
                            profiles.get_common_arcs()

    def test_parse_args_accepts_requested_count_and_character(self):
        module = load_generator()

        args = module.parse_args(["10", "--character", "김민정"])

        self.assertEqual(args.count, 10)
        self.assertEqual(args.character, "김민정")

    def test_parse_args_rejects_non_positive_count(self):
        module = load_generator()

        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                module.parse_args(["0"])

    def test_profiled_characters_uses_only_json_profiles(self):
        module = load_generator()

        characters = module.profiled_characters(module.load_characters())

        self.assertEqual([character.name for character in characters], list(REQUESTED_PLACES))

    def test_profiled_characters_rejects_unknown_character(self):
        module = load_generator()

        with self.assertRaisesRegex(ValueError, "JSON profile"):
            module.profiled_characters(module.load_characters(), "없는사람")

    def test_generate_outlines_writes_requested_count_with_only_profiled_character(self):
        module = load_generator()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            later_file = output_dir / "011화.txt"
            later_file.write_text("keep", encoding="utf-8")

            written = module.generate_outlines(3, output_dir=output_dir)

            self.assertEqual(
                [path.name for path in written],
                ["001화.txt", "002화.txt", "003화.txt"],
            )
            self.assertFalse((output_dir / "004화.txt").exists())
            self.assertEqual(later_file.read_text(encoding="utf-8"), "keep")
            for path, name in zip(written, list(REQUESTED_PLACES)[:3]):
                self.assertIn(f"- {name}", path.read_text(encoding="utf-8"))

    def test_get_profile_loads_json_named_after_the_character(self):
        import json

        from profiles import get_profile

        json_profile = json.loads(KIM_JSON_PATH.read_text(encoding="utf-8"))
        loaded_profile = get_profile("김민정")

        self.assertEqual(loaded_profile, json_profile)

    def test_kim_minjeong_profile_uses_place_details_events_without_arcs(self):
        from profiles import get_profile

        PROFILE = get_profile("김민정")

        self.assertEqual(PROFILE["name"], "김민정")
        self.assertEqual(len(PROFILE["events"]), 10)

        event = PROFILE["events"][0]
        self.assertEqual(event["place"], "고급호텔 스위트룸")
        self.assertIsInstance(event["weather"], str)
        self.assertIsInstance(event["pressure"], str)
        self.assertGreaterEqual(len(event["place_details"]), 1)
        self.assertNotIn("place_rules", event)
        self.assertGreaterEqual(len(event["outfit_pool"]), 10)
        self.assertGreaterEqual(len(event["hair_pool"]), 5)
        self.assertNotIn("arcs", event)
        self.assertIn("exposure_focus", event)
        self.assertTrue(any("애쉬브라운" in hair for hair in event["hair_pool"]))

        profile_text = "\n".join(event["outfit_pool"] + event["hair_pool"])
        self.assertNotIn("전기블루", profile_text)
        self.assertNotIn("블루 브릿지", profile_text)
        self.assertNotIn("파란 브릿지", profile_text)
        self.assertNotIn("파란 가닥", profile_text)

    def test_minjeong_events_use_requested_places_and_style_counts(self):
        from profiles import get_profile

        PROFILE = get_profile("김민정")
        requested_places = [
            "고급호텔 스위트룸",
            "고급호텔 실내 수영장",
            "고급호텔 라운지",
            "e스포츠 경기장 무대 뒤 통로",
            "심야 PC방 커플석",
            "중계 부스 옆 빈 관람석",
            "게임 행사장 물품 창고",
            "PC방 옥상",
            "뒤풀이 술집 구석자리",
            "무인 보드게임 카페",
        ]

        self.assertEqual([event["place"] for event in PROFILE["events"]], requested_places)
        for event in PROFILE["events"]:
            with self.subTest(place=event["place"]):
                self.assertGreaterEqual(len(event["outfit_pool"]), 10)
                self.assertGreaterEqual(len(event["hair_pool"]), 5)
                self.assertNotIn("arcs", event)

    def test_select_scene_prefers_events_without_requiring_arcs(self):
        module = load_generator()
        from profiles import get_common_arcs, get_profile

        PROFILE = get_profile("김민정")
        kim = next(char for char in module.load_characters() if char.name == "김민정")
        scene = module.select_scene(10, kim)

        event = PROFILE["events"][0]
        selected_arc = module.pick(
            get_common_arcs(),
            10,
            module.CHARACTER_ORDER.index("김민정") + 7,
        )

        self.assertEqual(scene["profile_name"], "김민정")
        self.assertNotIn("group", scene)
        self.assertEqual(scene["event_id"], "minjeong_luxury_hotel_suite")
        self.assertEqual(scene["place"], "고급호텔 스위트룸")
        self.assertEqual(scene["weather"], event["weather"])
        self.assertEqual(scene["pressure"], event["pressure"])
        self.assertEqual(scene["place_details"], event["place_details"])
        self.assertIn(scene["clothes"], event["outfit_pool"])
        self.assertIn(scene["hair"], event["hair_pool"])
        self.assertNotIn("전기블루", scene["clothes"] + scene["hair"])
        self.assertNotIn("블루 브릿지", scene["clothes"] + scene["hair"])
        self.assertNotIn("파란 브릿지", scene["clothes"] + scene["hair"])
        self.assertNotIn("파란 가닥", scene["clothes"] + scene["hair"])
        self.assertEqual(scene.get("arc_type"), selected_arc["type"])
        self.assertEqual(scene["start"], selected_arc["start"])
        self.assertEqual(scene["turn"], selected_arc["turn"])
        self.assertEqual(scene["after"], selected_arc["after"])

    def test_select_scene_rejects_character_without_json_profile(self):
        module = load_generator()
        character = module.Character(
            name="없는사람",
            profile="",
            position="",
            speech="",
            personality="",
            appearance="",
            points="",
        )

        with self.assertRaisesRegex(
            ValueError,
            "character JSON profile not found: 없는사람",
        ):
            module.select_scene(1, character)

    def test_select_scene_does_not_filter_common_arcs_by_type(self):
        import profiles

        common_arcs = {
            "arcs": [
                {
                    "type": "male_b",
                    "start": "첫 시작",
                    "turn": "첫 전환",
                    "after": "첫 여운",
                },
                {
                    "type": "unfiltered_custom_type",
                    "start": "둘째 시작",
                    "turn": "둘째 전환",
                    "after": "둘째 여운",
                },
            ]
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            common_arcs_path = Path(temporary_directory) / "common_arcs.json"
            import json

            common_arcs_path.write_text(
                json.dumps(common_arcs, ensure_ascii=False),
                encoding="utf-8",
            )
            with patch.object(profiles, "COMMON_ARCS_PATH", common_arcs_path):
                module = load_generator()
                kim = next(
                    char for char in module.load_characters() if char.name == "김민정"
                )
                scene = module.select_scene(2, kim)

        self.assertEqual(scene.get("arc_type"), "unfiltered_custom_type")
        self.assertEqual(
            (scene["start"], scene["turn"], scene["after"]),
            ("둘째 시작", "둘째 전환", "둘째 여운"),
        )

    def test_select_scene_repeats_the_same_common_arc_for_the_same_episode(self):
        module = load_generator()
        kim = next(char for char in module.load_characters() if char.name == "김민정")

        first = module.select_scene(7, kim)
        second = module.select_scene(7, kim)

        self.assertIsNotNone(first.get("arc_type"))
        self.assertEqual(
            (first.get("arc_type"), first["start"], first["turn"], first["after"]),
            (second.get("arc_type"), second["start"], second["turn"], second["after"]),
        )

    def test_events_use_place_details_without_legacy_place_rules(self):
        from profiles import get_profile

        PROFILE = get_profile("김민정")

        for event in PROFILE["events"]:
            with self.subTest(event_id=event["id"]):
                self.assertIn("place_details", event)
                self.assertIsInstance(event["place_details"], list)
                self.assertGreaterEqual(len(event["place_details"]), 1)
                self.assertNotIn("place_rules", event)

    def test_outline_text_renders_weather_without_duplicate_phrase(self):
        module = load_generator()
        kim = next(char for char in module.load_characters() if char.name == "김민정")
        scene = module.select_scene(1, kim)

        text = module.outline_text(1, kim, scene)

        self.assertNotIn("있다 분위기", text)
        self.assertIn(f"장소의 공기감은 {scene['weather']}.", text)

    def test_outline_text_renders_place_details_when_profile_provides_them(self):
        module = load_generator()
        kim = next(char for char in module.load_characters() if char.name == "김민정")
        scene = module.select_scene(10, kim)

        text = module.outline_text(10, kim, scene)

        self.assertIn("장소 디테일:", text)
        self.assertIn(", ".join(scene["place_details"]), text)


if __name__ == "__main__":
    unittest.main()
