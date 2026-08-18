# Common Scene Pools Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate outlines from common 60:40 work/indoor location pools and body-type outfit pools without character-specific JSON profiles.

**Architecture:** Expand `profiles/common_arcs.json` into the single common scene configuration while retaining its existing `arcs`. Parse body type directly from each character text file, select scene type with an injected random source, then select a matching common location and body-type outfit before rendering.

**Tech Stack:** Python 3 standard library (`json`, `random`, `unittest`, `tempfile`, `pathlib`)

**Spec:** `docs/superpowers/specs/2026-08-18-common-scene-pools-design.md`

## Global Constraints

- Keep the existing `arcs` entries and deterministic arc selection unchanged.
- Use `work: 60` and `indoor: 40` as the exact scene-type weights.
- Do not restore or read character-specific JSON profiles.
- Do not add profession-specific uniforms or profession mapping.
- Read body type from the `- 체형:` field in `characters/<name>.txt`.
- Preserve the existing CLI interfaces for `generate_outlines.py` and `run_pipeline.py`.
- Do not execute `run_pipeline.py` during tests because it commits and pushes automatically.

---

### Task 1: Expanded Common Scene Configuration

**Files:**
- Modify: `profiles/common_arcs.json`
- Modify: `profiles/__init__.py`
- Create: `tests/test_common_scene_config.py`

**Interfaces:**
- Produces: `get_common_scene_config() -> dict[str, Any]`
- Preserves: `get_common_arcs() -> list[dict[str, str]]`
- Configuration keys: `scene_type_weights`, `locations`, `outfits`, `arcs`

- [ ] **Step 1: Write failing loader and validation tests**

```python
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import profiles


class CommonSceneConfigTests(unittest.TestCase):
    def test_real_config_contains_complete_scene_pools(self):
        config = profiles.get_common_scene_config()

        self.assertEqual(config["scene_type_weights"], {"work": 60, "indoor": 40})
        self.assertEqual(
            [location["place"] for location in config["locations"]["work"]],
            ["퇴근 후 호텔", "비상계단", "사옥 옥상", "건물 화장실"],
        )
        self.assertEqual(
            [location["place"] for location in config["locations"]["indoor"]],
            ["호텔 객실", "실내 수영장", "호텔 욕실"],
        )
        expected_body_types = {
            "아담", "늘씬", "글래머", "근육", "육감", "저신장글래머", "빈유슬렌더"
        }
        self.assertEqual(set(config["outfits"]), expected_body_types)
        for body_type in expected_body_types:
            self.assertGreaterEqual(len(config["outfits"][body_type]["work"]), 3)
            self.assertGreaterEqual(len(config["outfits"][body_type]["indoor"]), 3)

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
```

- [ ] **Step 2: Run tests and verify the expected failure**

Run: `python3 -m unittest tests.test_common_scene_config -v`

Expected: FAIL because `get_common_scene_config` does not exist and the JSON has no common scene pools.

- [ ] **Step 3: Add the common JSON values**

Keep the existing `arcs` array byte-for-byte in meaning and add this structure around it:

```json
{
  "scene_type_weights": {"work": 60, "indoor": 40},
  "locations": {
    "work": [
      {"id": "after_work_hotel", "place": "퇴근 후 호텔", "weather_pool": ["야근 뒤 열기가 남은 밤", "비가 그친 늦은 밤"], "pressure": "퇴근 일정이 끝난 뒤 두 사람만 같은 호텔 동선에 남는다", "place_details": ["닫힌 객실 문", "침대 옆 업무 가방", "창밖의 늦은 도심 불빛"]},
      {"id": "emergency_stairs", "place": "비상계단", "weather_pool": ["냉방 소리가 멀어진 늦은 밤", "습한 여름 저녁"], "pressure": "사람이 드문 층계참과 닫힌 방화문이 둘의 동선을 고립시킨다", "place_details": ["회색 방화문", "층계참 비상등", "난간 아래 긴 계단"]},
      {"id": "office_rooftop", "place": "사옥 옥상", "weather_pool": ["열기가 식는 여름밤", "바람이 강한 흐린 저녁"], "pressure": "퇴근 시간이 지나 잠긴 출입문과 빈 옥상이 둘만의 공간이 된다", "place_details": ["옥상 출입문", "낮은 안전 난간", "도심 간판 불빛"]},
      {"id": "building_restroom", "place": "건물 화장실", "weather_pool": ["늦은 밤의 건조한 냉방", "장맛비가 들리는 저녁"], "pressure": "마감 뒤 인적이 끊긴 층의 화장실에 두 사람만 남는다", "place_details": ["빈 세면대", "잠긴 출입문", "차가운 타일 바닥"]}
    ],
    "indoor": [
      {"id": "hotel_room", "place": "호텔 객실", "weather_pool": ["비가 창문을 두드리는 밤", "무더운 여름밤"], "pressure": "닫힌 객실 문과 늦은 시간이 바깥으로 돌아갈 이유를 줄인다", "place_details": ["정돈된 침대", "커튼 사이 도심 불빛", "테이블 위 카드키"]},
      {"id": "indoor_pool", "place": "실내 수영장", "weather_pool": ["습기가 감도는 늦은 저녁", "비 오는 날의 흐린 채광"], "pressure": "운영 시간이 끝나 물소리만 남은 수영장에 둘이 머문다", "place_details": ["젖은 타일", "잔잔한 수면", "정리된 선베드"]},
      {"id": "hotel_bathroom", "place": "호텔 욕실", "weather_pool": ["더운 물의 김이 남은 밤", "빗소리가 희미하게 들리는 새벽"], "pressure": "수증기와 닫힌 문이 좁은 공간의 거리를 빠르게 줄인다", "place_details": ["김이 서린 거울", "젖은 대리석", "접힌 흰 수건"]}
    ]
  },
  "outfits": {
    "아담": {"work": ["몸에 과하게 붙지 않는 반팔 블라우스와 하이웨이스트 H라인 스커트", "짧은 재킷과 발목이 드러나는 슬림 슬랙스", "허리선이 단정한 셔츠 원피스와 낮은 굽 구두"], "indoor": ["가벼운 크롭 카디건과 하이웨이스트 쇼츠", "허리선이 잡힌 미니 원피스와 얇은 샌들", "심플한 원피스 수영복과 얇은 로브"]},
    "늘씬": {"work": ["세로선이 긴 블라우스와 스트레이트 슬랙스", "무릎 아래로 떨어지는 셔츠 원피스와 슬링백", "얇은 재킷과 롱 펜슬 스커트"], "indoor": ["긴 실루엣의 슬립 원피스", "홀터넥 수영복과 가벼운 로브", "민소매 니트와 와이드 팬츠"]},
    "글래머": {"work": ["가슴선을 단정하게 잡는 블라우스와 허리선이 높은 펜슬 스커트", "허리를 묶는 재킷 원피스", "부드러운 니트와 하이웨이스트 슬랙스"], "indoor": ["곡선을 따라 흐르는 랩 원피스", "지지력이 있는 원피스 수영복과 시어 로브", "새틴 캐미솔과 편안한 와이드 팬츠"]},
    "근육": {"work": ["어깨선이 정돈된 셔츠와 활동적인 테이퍼드 팬츠", "신축성 있는 반팔 재킷과 슬림 스커트", "민소매 이너와 가벼운 셋업 팬츠"], "indoor": ["탄탄한 중심이 드러나는 슬리브리스 톱과 조거 팬츠", "스포티한 원피스 수영복과 집업 로브", "크롭 티셔츠와 편안한 쇼츠"]},
    "육감": {"work": ["부드러운 곡선을 정돈하는 셔링 블라우스와 세미와이드 슬랙스", "허리를 가볍게 묶는 미디 원피스", "단정한 브이넥 니트와 롱 스커트"], "indoor": ["몸선을 조이지 않고 흐르는 새틴 원피스", "와이드 스트랩 원피스 수영복과 로브", "부드러운 캐미솔과 랩 스커트"]},
    "저신장글래머": {"work": ["상체를 단정히 잡는 짧은 재킷과 하이웨이스트 스커트", "허리선이 높은 셔츠 원피스와 낮은 슬링백", "슬림 니트와 발목이 보이는 테이퍼드 팬츠"], "indoor": ["짧은 랩 원피스와 얇은 샌들", "하이컷 원피스 수영복과 짧은 로브", "크롭 카디건과 하이웨이스트 쇼츠"]},
    "빈유슬렌더": {"work": ["얇은 셔츠와 일자로 떨어지는 슬랙스", "작은 칼라의 미니멀한 원피스", "가벼운 재킷과 플리츠 미디스커트"], "indoor": ["담백한 캐미솔 원피스", "심플한 홀터넥 수영복과 얇은 셔츠", "루즈한 니트와 짧은 쇼츠"]}
  },
  "arcs": []
}
```

The shown empty `arcs` is only the insertion position: retain all current arc objects instead of replacing them.

- [ ] **Step 4: Implement validated loading**

```python
from typing import Any

SCENE_TYPES = ("work", "indoor")
BODY_TYPES = (
    "아담", "늘씬", "글래머", "근육", "육감", "저신장글래머", "빈유슬렌더"
)
LOCATION_FIELDS = {"id", "place", "weather_pool", "pressure", "place_details"}


def get_common_scene_config() -> dict[str, Any]:
    try:
        payload = json.loads(COMMON_ARCS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"failed to load common scene config: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("common scene config must be an object")
    if payload.get("scene_type_weights") != {"work": 60, "indoor": 40}:
        raise ValueError("scene_type_weights must be work=60 and indoor=40")

    locations = payload.get("locations")
    if not isinstance(locations, dict):
        raise ValueError("locations must be an object")
    for scene_type in SCENE_TYPES:
        entries = locations.get(scene_type)
        if not isinstance(entries, list) or not entries:
            raise ValueError(f"locations.{scene_type} must be a non-empty list")
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict) or set(entry) != LOCATION_FIELDS:
                raise ValueError(f"locations.{scene_type}[{index}] has invalid fields")
            if not all(entry[field] for field in LOCATION_FIELDS):
                raise ValueError(f"locations.{scene_type}[{index}] has blank fields")

    outfits = payload.get("outfits")
    if not isinstance(outfits, dict) or set(outfits) != set(BODY_TYPES):
        raise ValueError("outfits must contain every supported body type")
    for body_type in BODY_TYPES:
        pools = outfits[body_type]
        if not isinstance(pools, dict) or set(pools) != set(SCENE_TYPES):
            raise ValueError(f"outfits.{body_type} must contain work and indoor")
        for scene_type in SCENE_TYPES:
            if not isinstance(pools[scene_type], list) or not pools[scene_type]:
                raise ValueError(f"outfits.{body_type}.{scene_type} must be a non-empty list")

    _validated_arcs(payload.get("arcs"))
    return payload


def get_common_arcs() -> list[dict[str, str]]:
    return get_common_scene_config()["arcs"]
```

Extract the existing arc-loop checks into `_validated_arcs(arcs)` so the validation remains defined once.

- [ ] **Step 5: Run tests and validate JSON**

Run: `python3 -m unittest tests.test_common_scene_config -v`

Expected: 2 tests pass.

Run: `python3 -m json.tool profiles/common_arcs.json >/dev/null`

Expected: exit code 0.

- [ ] **Step 6: Commit the common configuration**

```bash
git add profiles/common_arcs.json profiles/__init__.py tests/test_common_scene_config.py
git commit -m "Add common location and outfit pools"
```

---

### Task 2: Character Text Based Eligibility

**Files:**
- Modify: `generate_outlines.py`
- Create: `tests/test_common_outline_generation.py`

**Interfaces:**
- Consumes: `get_common_scene_config() -> dict[str, Any]`
- Produces: `Character.body_type: str`
- Produces: `selectable_characters(characters: list[Character], character_name: str | None = None) -> list[Character]`

- [ ] **Step 1: Write failing character-selection tests**

```python
import unittest
from pathlib import Path

import generate_outlines


class CommonOutlineGenerationTests(unittest.TestCase):
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
        selected = generate_outlines.selectable_characters(characters, "김나영")
        self.assertEqual([char.name for char in selected], ["김나영"])
```

- [ ] **Step 2: Run tests and verify the expected failure**

Run: `python3 -m unittest tests.test_common_outline_generation -v`

Expected: FAIL because `Character` has no `body_type`, and selection still requires deleted JSON profiles.

- [ ] **Step 3: Parse body type and remove profile eligibility checks**

```python
from profiles import get_common_arcs, get_common_scene_config


@dataclass(frozen=True)
class Character:
    name: str
    profile: str
    position: str
    body_type: str
    speech: str
    personality: str
    appearance: str
    points: str


def load_characters() -> list[Character]:
    characters = []
    for name in character_names():
        path = CHARACTER_DIR / f"{name}.txt"
        profile = path.read_text(encoding="utf-8").strip()
        body_type = bullet_value(profile, "체형")
        if not body_type:
            raise ValueError(f"character body type not found: {name}")
        characters.append(
            Character(
                name=name,
                profile=profile,
                position=bullet_value(profile, "리부트 포지션"),
                body_type=body_type,
                speech=first_sentence(section(profile, "말투")),
                personality=first_sentence(section(profile, "성격")),
                appearance=first_sentence(section(profile, "외형")),
                points=section(profile, "장면 활용 포인트").replace("\n", " "),
            )
        )
    return characters


def selectable_characters(
    characters: list[Character],
    character_name: str | None = None,
) -> list[Character]:
    if character_name is None:
        if not characters:
            raise ValueError("no character text profiles found")
        return characters
    selected = [character for character in characters if character.name == character_name]
    if not selected:
        raise ValueError(f"character text profile not found: {character_name}")
    return selected
```

Update `generate_outlines()` to call `selectable_characters()`.

- [ ] **Step 4: Run character-selection tests**

Run: `python3 -m unittest tests.test_common_outline_generation -v`

Expected: 3 tests pass.

- [ ] **Step 5: Commit character text selection**

```bash
git add generate_outlines.py tests/test_common_outline_generation.py
git commit -m "Generate from character text profiles"
```

---

### Task 3: Weighted Scene And Outfit Selection

**Files:**
- Modify: `generate_outlines.py`
- Modify: `tests/test_common_outline_generation.py`

**Interfaces:**
- Consumes: `get_common_scene_config() -> dict[str, Any]`
- Changes: `select_scene(ep: int, char: Character, rng: random.Random | None = None) -> dict[str, Any]`
- Changes: `generate_outlines(count: int, character_name: str | None = None, output_dir: Path = OUTLINE_DIR, rng: random.Random | None = None) -> list[Path]`

- [ ] **Step 1: Write failing weighted-selection tests**

```python
import random
import tempfile
from dataclasses import replace


class ChoiceRecorder(random.Random):
    def __init__(self, selected_scene_type):
        super().__init__(0)
        self.selected_scene_type = selected_scene_type
        self.weight_call = None

    def choices(self, population, weights=None, *, cum_weights=None, k=1):
        self.weight_call = (list(population), list(weights), k)
        return [self.selected_scene_type]


class CommonOutlineGenerationTests(unittest.TestCase):
    def test_select_scene_uses_work_60_indoor_40(self):
        char = next(char for char in generate_outlines.load_characters() if char.name == "김나영")
        rng = ChoiceRecorder("work")
        scene = generate_outlines.select_scene(1, char, rng)

        self.assertEqual(rng.weight_call, (["work", "indoor"], [60, 40], 1))
        self.assertEqual(scene["scene_type"], "work")
        self.assertIn(scene["place"], {"퇴근 후 호텔", "비상계단", "사옥 옥상", "건물 화장실"})

    def test_select_scene_uses_matching_body_type_outfit(self):
        char = next(char for char in generate_outlines.load_characters() if char.name == "김나영")
        config = generate_outlines.get_common_scene_config()
        scene = generate_outlines.select_scene(1, char, ChoiceRecorder("indoor"))

        self.assertEqual(char.body_type, "저신장글래머")
        self.assertIn(scene["clothes"], config["outfits"]["저신장글래머"]["indoor"])
        self.assertEqual(scene["hair"], "캐릭터 프로필에 명시된 고유 헤어스타일을 유지한다")

    def test_select_scene_rejects_unsupported_body_type(self):
        char = next(char for char in generate_outlines.load_characters() if char.name == "김나영")
        unsupported = replace(char, body_type="알수없음")
        with self.assertRaisesRegex(ValueError, "unsupported character body type"):
            generate_outlines.select_scene(1, unsupported, ChoiceRecorder("work"))

    def test_generate_outlines_writes_without_character_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            written = generate_outlines.generate_outlines(
                2,
                output_dir=Path(temp_dir),
                rng=random.Random(7),
            )
            self.assertEqual([path.name for path in written], ["001화.txt", "002화.txt"])
            self.assertTrue(all("이번 씬 복장:" in path.read_text(encoding="utf-8") for path in written))
```

- [ ] **Step 2: Run tests and verify the expected failure**

Run: `python3 -m unittest tests.test_common_outline_generation -v`

Expected: FAIL because `select_scene` still loads deleted character JSON and accepts no random source.

- [ ] **Step 3: Implement weighted common scene selection**

```python
def select_scene(
    ep: int,
    char: Character,
    rng: random.Random | None = None,
) -> dict[str, Any]:
    chooser = rng or random.Random()
    config = get_common_scene_config()
    names = character_names()
    character_index = names.index(char.name) if char.name in names else 0
    weights = config["scene_type_weights"]
    scene_types = ["work", "indoor"]
    scene_type = chooser.choices(
        scene_types,
        weights=[weights[name] for name in scene_types],
        k=1,
    )[0]
    location = chooser.choice(config["locations"][scene_type])
    outfit_pool = config["outfits"].get(char.body_type)
    if outfit_pool is None:
        raise ValueError(f"unsupported character body type: {char.name}: {char.body_type}")
    arc = pick(get_common_arcs(), ep, character_index + 7)

    return {
        "scene_type": scene_type,
        "place": location["place"],
        "weather": chooser.choice(location["weather_pool"]),
        "pressure": location["pressure"],
        "place_details": location["place_details"],
        "clothes": chooser.choice(outfit_pool[scene_type]),
        "hair": "캐릭터 프로필에 명시된 고유 헤어스타일을 유지한다",
        "arc_type": arc["type"],
        "start": arc["start"],
        "turn": arc["turn"],
        "after": arc["after"],
        "profile_name": char.name,
        "event_id": location["id"],
        "event_set_id": location["id"],
    }
```

In `generate_outlines()`, create `chooser = rng or random.Random()`, use
`chooser.shuffle(shuffled_pool)`, and call `select_scene(ep, char, chooser)`.

- [ ] **Step 4: Run focused and full tests**

Run: `python3 -m unittest tests.test_common_scene_config tests.test_common_outline_generation tests.test_footer_resources -v`

Expected: all tests pass.

- [ ] **Step 5: Run a safe CLI smoke test**

The existing CLI has no `--output-dir`, so perform the smoke test through
Python to avoid overwriting the user's `outlines` directory:

```bash
python3 - <<'PY'
import random
import tempfile
from pathlib import Path
from generate_outlines import generate_outlines

with tempfile.TemporaryDirectory() as temp_dir:
    paths = generate_outlines(10, output_dir=Path(temp_dir), rng=random.Random(18))
    assert len(paths) == 10
    assert all(path.exists() for path in paths)
    print("generated", len(paths), "temporary outlines")
PY
```

Expected: `generated 10 temporary outlines` and exit code 0.

- [ ] **Step 6: Check syntax, JSON, and whitespace**

Run:

```bash
python3 -m py_compile profiles/__init__.py generate_outlines.py
python3 -m json.tool profiles/common_arcs.json >/dev/null
git diff --check
```

Expected: all commands exit 0.

- [ ] **Step 7: Commit weighted scene generation**

```bash
git add generate_outlines.py tests/test_common_outline_generation.py
git commit -m "Select weighted common scenes and outfits"
```
