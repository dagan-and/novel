# Common Arcs JSON Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Load all shared scene arcs from `profiles/common_arcs.json` and combine one unfiltered arc with each selected character event.

**Architecture:** The `profiles` package owns JSON loading and validation through a `get_common_arcs()` function. `generate_outlines.py` asks that loader for the shared list in both scene-selection branches, then uses the existing deterministic `pick` function and exposes the selected metadata as `arc_type`.

**Tech Stack:** Python 3 standard library (`json`, `pathlib`, `unittest`), JSON data files

## Global Constraints

- `profiles/common_arcs.json` is the single source of truth for shared arcs.
- Every arc has non-empty string fields named `type`, `start`, `turn`, and `after`.
- `type` is preserved as metadata and never filters or weights selection.
- Repeating the same episode and character with unchanged arc ordering selects the same arc.
- Invalid or missing common-arc data raises a clear error without a hard-coded fallback.
- Character event objects do not contain local `arcs`.

---

### Task 1: Common Arc Data Loader

**Files:**
- Create: `profiles/common_arcs.json`
- Modify: `profiles/__init__.py`
- Test: `tests/test_profiles.py`

**Interfaces:**
- Consumes: `JSON_PROFILE_DIR: pathlib.Path`
- Produces: `get_common_arcs() -> list[dict[str, str]]`

- [x] **Step 1: Write failing loader tests**

Add tests that load the real common file, verify all four required string fields, and temporarily override `profiles.COMMON_ARCS_PATH` to verify missing files, empty `arcs`, and malformed entries raise `ValueError` messages containing `common arcs`.

```python
def test_get_common_arcs_loads_non_empty_validated_arcs(self):
    from profiles import get_common_arcs

    arcs = get_common_arcs()

    self.assertGreaterEqual(len(arcs), 1)
    for arc in arcs:
        self.assertEqual(set(arc), {"type", "start", "turn", "after"})
        for key in ("type", "start", "turn", "after"):
            self.assertIsInstance(arc[key], str)
            self.assertTrue(arc[key].strip())
```

- [x] **Step 2: Run loader tests and verify RED**

Run: `python3 -m unittest tests.test_profiles.CharacterProfileTests.test_get_common_arcs_loads_non_empty_validated_arcs`

Expected: FAIL because `get_common_arcs` does not exist.

- [x] **Step 3: Add the common JSON and minimal validated loader**

Create `profiles/common_arcs.json` with the four arcs currently stored in `SCENE_ARCS`, adding `"type": "male_b"` to every entry. Implement:

```python
COMMON_ARCS_PATH = JSON_PROFILE_DIR / "common_arcs.json"
COMMON_ARC_FIELDS = ("type", "start", "turn", "after")

def get_common_arcs() -> list[dict[str, str]]:
    try:
        payload = json.loads(COMMON_ARCS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"failed to load common arcs: {exc}") from exc

    arcs = payload.get("arcs") if isinstance(payload, dict) else None
    if not isinstance(arcs, list) or not arcs:
        raise ValueError("common arcs must be a non-empty list")
    for index, arc in enumerate(arcs):
        if not isinstance(arc, dict) or set(arc) != set(COMMON_ARC_FIELDS):
            raise ValueError(f"common arcs entry {index} has invalid fields")
        if any(not isinstance(arc[key], str) or not arc[key].strip() for key in COMMON_ARC_FIELDS):
            raise ValueError(f"common arcs entry {index} has blank fields")
    return arcs
```

- [x] **Step 4: Run focused loader tests and verify GREEN**

Run: `python3 -m unittest tests.test_profiles.CharacterProfileTests.test_get_common_arcs_loads_non_empty_validated_arcs`

Expected: PASS.

### Task 2: Generator Composition

**Files:**
- Modify: `generate_outlines.py`
- Modify: `tests/test_profiles.py`

**Interfaces:**
- Consumes: `profiles.get_common_arcs() -> list[dict[str, str]]`
- Produces: `select_scene(ep: int, char: Character) -> dict[str, Any]` with `arc_type`, `start`, `turn`, and `after`

- [x] **Step 1: Write failing composition tests**

Replace assertions against `module.SCENE_ARCS` with assertions against `get_common_arcs()`. Assert that `scene["arc_type"]` equals the selected entry's `type`, all selected arc values come from one common entry, event JSON has no `arcs`, and two calls with the same episode and character return the same four arc values.

```python
selected_arc = module.pick(
    get_common_arcs(),
    10,
    module.CHARACTER_ORDER.index("윤수빈") + 7,
)
self.assertEqual(scene["arc_type"], selected_arc["type"])
self.assertEqual(scene["start"], selected_arc["start"])
self.assertEqual(scene["turn"], selected_arc["turn"])
self.assertEqual(scene["after"], selected_arc["after"])
```

- [x] **Step 2: Run composition tests and verify RED**

Run: `python3 -m unittest tests.test_profiles.CharacterProfileTests.test_select_scene_prefers_events_without_requiring_arcs`

Expected: FAIL because `select_scene` does not expose `arc_type` and still references `SCENE_ARCS`.

- [x] **Step 3: Connect the generator and remove hard-coded arcs**

Import `get_common_arcs`, delete `SCENE_ARCS`, load the common list once per `select_scene` call, and use it in both profile-backed and legacy branches:

```python
common_arcs = get_common_arcs()
arc = pick(common_arcs, ep, CHARACTER_ORDER.index(char.name) + 7)
```

Add `"arc_type": arc["type"]` beside the three narrative arc fields in both returned scene dictionaries.

- [x] **Step 4: Run profile tests and verify GREEN**

Run: `python3 -m unittest tests/test_profiles.py`

Expected: all profile tests PASS.

- [x] **Step 5: Run full verification**

Run: `python3 -m unittest discover -s tests`

Expected: all tests PASS.

Run: `python3 generate_outlines.py 1 --character 윤수빈`

Expected: one outline is generated successfully using a common JSON arc.
