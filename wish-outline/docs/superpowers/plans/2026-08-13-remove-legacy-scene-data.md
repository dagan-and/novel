# Remove Legacy Scene Data Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove unused built-in scene data so character JSON profiles are the only source of event and styling information.

**Architecture:** `select_scene()` requires a character JSON profile containing `events`, combines that event with `profiles/common_arcs.json`, and returns no legacy group metadata. All group-based locations, outfits, hairstyles, compatibility helpers, and fallback branches are deleted from the generator.

**Tech Stack:** Python 3 standard library, JSON, `unittest`

## Global Constraints

- Character description text remains in `characters/<name>.txt`.
- Character-specific event and styling data comes only from `profiles/<name>.json`.
- Narrative arc data comes only from `profiles/common_arcs.json`.
- A missing JSON profile raises a clear `ValueError`.
- Events use `place_details`; `place_rules` compatibility is removed.
- Scene results do not contain `group`.

---

### Task 1: JSON-Only Scene Selection

**Files:**
- Modify: `tests/test_profiles.py`
- Modify: `generate_outlines.py`

**Interfaces:**
- Consumes: `get_profile(char.name) -> dict | None`, `get_common_arcs() -> list[dict[str, str]]`
- Produces: `select_scene(ep: int, char: Character) -> dict[str, Any]`

- [x] **Step 1: Write failing behavior tests**

Add one test asserting direct `select_scene()` use for `노은화` raises
`ValueError("character JSON profile not found: 노은화")`. Add one assertion to
the existing 윤수빈 selection test that the returned scene has no `group` key.

```python
def test_select_scene_rejects_character_without_json_profile(self):
    module = load_generator()
    character = next(char for char in module.load_characters() if char.name == "노은화")

    with self.assertRaisesRegex(ValueError, "character JSON profile not found: 노은화"):
        module.select_scene(1, character)
```

- [x] **Step 2: Run the focused tests and verify RED**

Run: `python3 -m unittest tests.test_profiles.CharacterProfileTests.test_select_scene_rejects_character_without_json_profile tests.test_profiles.CharacterProfileTests.test_select_scene_prefers_events_without_requiring_arcs`

Expected: FAIL because the legacy branch returns a scene for 노은화 and 윤수빈's result still contains `group`.

- [x] **Step 3: Remove legacy data and simplify selection**

Delete `SCENE_SETS`, `CHARACTER_GROUPS`, `LUXURY_HOTEL_LOCATIONS`,
`LOCATION_POOLS`, `OUTFIT_POOLS`, and `HAIR_VARIANTS`. Delete `hair_kind()` and
`outfit_group()`.

Replace `event_place_details()` with direct access inside `select_scene()` and
make the function profile-only:

```python
def select_scene(ep: int, char: Character) -> dict[str, Any]:
    profile = get_profile(char.name)
    if not profile or "events" not in profile:
        raise ValueError(f"character JSON profile not found: {char.name}")

    salt = CHARACTER_ORDER.index(char.name)
    event = pick(profile["events"], ep, salt)
    arc = pick(get_common_arcs(), ep, salt + 7)
    return {
        "place": event["place"],
        "weather": event["weather"],
        "pressure": event["pressure"],
        "place_details": event["place_details"],
        "clothes": pick(event["outfit_pool"], ep, salt + 3),
        "hair": pick(event["hair_pool"], ep, salt + 5),
        "arc_type": arc["type"],
        "start": arc["start"],
        "turn": arc["turn"],
        "after": arc["after"],
        "profile_name": profile["name"],
        "event_id": event["id"],
        "event_set_id": event["id"],
    }
```

- [x] **Step 4: Run focused and full tests and verify GREEN**

Run: `python3 -m unittest tests/test_profiles.py`

Expected: all profile tests PASS.

Run: `python3 -m unittest discover -s tests`

Expected: all tests PASS.

- [x] **Step 5: Verify removal and generation**

Run: `rg -n "SCENE_SETS|CHARACTER_GROUPS|LUXURY_HOTEL_LOCATIONS|LOCATION_POOLS|OUTFIT_POOLS|HAIR_VARIANTS|hair_kind|outfit_group|place_rules" generate_outlines.py`

Expected: no matches.

Run: `python3 generate_outlines.py 1 --character 윤수빈`

Expected: one outline file is generated successfully.
