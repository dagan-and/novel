import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import profiles


def common_scene_payload():
    return json.loads(profiles.COMMON_ARCS_PATH.read_text(encoding="utf-8"))


class CommonSceneConfigTests(unittest.TestCase):
    def test_scene_config_accepts_missing_arcs(self):
        payload = common_scene_payload()
        payload.pop("arcs", None)

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "common_arcs.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with patch.object(profiles, "COMMON_ARCS_PATH", path):
                config = profiles.get_common_scene_config()

        self.assertEqual(config["arcs"], [])

    def test_scene_config_accepts_empty_arcs(self):
        payload = common_scene_payload()
        payload["arcs"] = []

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "common_arcs.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with patch.object(profiles, "COMMON_ARCS_PATH", path):
                config = profiles.get_common_scene_config()

        self.assertEqual(config["arcs"], [])

    def test_real_config_contains_complete_scene_pools(self):
        config = profiles.get_common_scene_config()

        self.assertEqual(config["scene_type_weights"], {"work": 60, "indoor": 40})
        self.assertEqual(
            [location["place"] for location in config["locations"]["work"]],
            [
                "밀폐형 프라이빗 회의 부스",
                "어두운 힙한 카페 화장실",
                "불 꺼진 1층 통유리 사무실",
                "건물 비상계단 층계참",
                "지하주차장 구석 차 안",
                "늦은 밤 퇴근 골목길 구석",
                "멈춰 선 전용 엘리베이터",
                "빌딩 옥상 출입구 앞",
            ],
        )
        self.assertEqual(
            [location["place"] for location in config["locations"]["indoor"]],
            [
                "주말 호텔 침실",
                "수증기 가득한 욕실",
                "자취방 침대 위",
                "동네 코인세탁소",
                "자취방 앞 편의점 뒷골목",
                "자취방 공용 계단",
            ],
        )
        expected_body_types = {
            "슬림글래머",
            "아담글래머",
            "늘씬한슬림",
            "균형잡힌비율",
            "가녀린슬렌더",
            "탄탄한스포티",
        }
        self.assertEqual(set(config["outfits"]), expected_body_types)
        for body_type in expected_body_types:
            self.assertGreaterEqual(len(config["outfits"][body_type]["work"]), 8)
            self.assertGreaterEqual(len(config["outfits"][body_type]["indoor"]), 8)
            self.assertFalse(
                any(
                    "수영복" in outfit
                    for scene_type in ("work", "indoor")
                    for outfit in config["outfits"][body_type][scene_type]
                )
            )

    def test_loader_rejects_missing_scene_type_pool(self):
        invalid = {
            "scene_type_weights": {"work": 60, "indoor": 40},
            "locations": {"work": [], "indoor": []},
            "outfits": {},
            "arcs": [{"type": "x", "start": "s", "turn": "t", "after": "a"}],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "common_arcs.json"
            path.write_text(json.dumps(invalid), encoding="utf-8")
            with patch.object(profiles, "COMMON_ARCS_PATH", path):
                with self.assertRaisesRegex(ValueError, "locations.work must be a non-empty list"):
                    profiles.get_common_scene_config()

    def test_loader_rejects_nonblank_string_location_fields(self):
        for field, value in (("id", " "), ("place", 1), ("pressure", "")):
            with self.subTest(field=field):
                payload = common_scene_payload()
                payload["locations"]["work"][0][field] = value

                with tempfile.TemporaryDirectory() as temp_dir:
                    path = Path(temp_dir) / "common_arcs.json"
                    path.write_text(json.dumps(payload), encoding="utf-8")
                    with patch.object(profiles, "COMMON_ARCS_PATH", path):
                        with self.assertRaisesRegex(
                            ValueError,
                            rf"locations.work\[0\].{field} must be a non-blank string",
                        ):
                            profiles.get_common_scene_config()

    def test_loader_rejects_location_pool_that_is_not_a_list(self):
        payload = common_scene_payload()
        payload["locations"]["work"][0]["weather_pool"] = "late night"

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "common_arcs.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with patch.object(profiles, "COMMON_ARCS_PATH", path):
                with self.assertRaisesRegex(
                    ValueError,
                    r"locations.work\[0\].weather_pool must be a non-empty list of non-blank strings",
                ):
                    profiles.get_common_scene_config()

    def test_loader_rejects_location_pool_with_blank_string_item(self):
        payload = common_scene_payload()
        payload["locations"]["work"][0]["place_details"] = ["door", " "]

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "common_arcs.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with patch.object(profiles, "COMMON_ARCS_PATH", path):
                with self.assertRaisesRegex(
                    ValueError,
                    r"locations.work\[0\].place_details must be a non-empty list of non-blank strings",
                ):
                    profiles.get_common_scene_config()

    def test_loader_rejects_outfit_pool_that_is_not_a_list(self):
        payload = common_scene_payload()
        payload["outfits"]["슬림글래머"]["work"] = "blouse"

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "common_arcs.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with patch.object(profiles, "COMMON_ARCS_PATH", path):
                with self.assertRaisesRegex(
                    ValueError,
                    r"outfits.슬림글래머.work must be a non-empty list of non-blank strings",
                ):
                    profiles.get_common_scene_config()

    def test_loader_rejects_outfit_pool_with_blank_string_item(self):
        payload = common_scene_payload()
        payload["outfits"]["슬림글래머"]["indoor"] = ["robe", " "]

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "common_arcs.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with patch.object(profiles, "COMMON_ARCS_PATH", path):
                with self.assertRaisesRegex(
                    ValueError,
                    r"outfits.슬림글래머.indoor must be a non-empty list of non-blank strings",
                ):
                    profiles.get_common_scene_config()

    def test_get_common_arcs_accepts_arcs_only_payload(self):
        expected = [{"type": "x", "start": "s", "turn": "t", "after": "a"}]
        payload = {"arcs": expected}

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "common_arcs.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with patch.object(profiles, "COMMON_ARCS_PATH", path):
                self.assertEqual(profiles.get_common_arcs(), expected)
