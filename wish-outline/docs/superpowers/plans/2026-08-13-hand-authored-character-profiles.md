# Hand-Authored Character Profiles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add complete, individually authored JSON scene profiles for the remaining 19 adult characters.

**Architecture:** Each character receives a standalone `profiles/<name>.json` matching the existing 윤수빈 schema. Content is authored directly from the corresponding character file and requested place list; no builder, shared styling template, or runtime generator is added.

**Tech Stack:** JSON, Python 3 standard library, `unittest`, `jq`

## Global Constraints

- Preserve the exact ten requested places and their order for every character.
- Write exactly ten unique outfit descriptions and five unique hair descriptions per event.
- Every outfit description includes outfit, makeup, shoes, accessories, fabric or fit, and exposure intent.
- Respect each character's established haircut, color, personality, occupation, and proportions.
- Customize shared hotel locations independently for every character.
- Do not add `arcs`, `place_rules`, a builder script, or shared styling templates.
- Do not modify `profiles/윤수빈.json`.

---

### Task 1: Collection Contract Tests

**Files:**
- Modify: `tests/test_profiles.py`

**Interfaces:**
- Consumes: `profiles/<name>.json`
- Produces: collection-wide validation for the 20 character profiles

- [x] Add literal expected place lists for all 20 characters and tests for file existence, exact order, required event keys, exact 10/5 counts, non-empty unique strings, no `arcs` or `place_rules`, global exact-string uniqueness, and successful `select_scene()` for every character.
- [x] Run `python3 -m unittest tests.test_profiles.CharacterProfileTests.test_all_character_profiles_match_the_requested_contract` and confirm failure because 19 profiles are absent.

### Task 2: Hospitality, Aviation, And Food Profiles

**Files:**
- Create: `profiles/노은화.json`
- Create: `profiles/도하영.json`
- Create: `profiles/박미현.json`
- Create: `profiles/차소연.json`
- Create: `profiles/최윤서.json`
- Create: `profiles/한소희.json`

**Interfaces:**
- Produces: six standalone profiles with ten authored events each

- [x] Author all six profiles directly from their character files and requested places.
- [x] Run the collection contract test and confirm only profiles from later tasks remain missing.

### Task 3: Art, Music, Dance, And Photography Profiles

**Files:**
- Create: `profiles/문아영.json`
- Create: `profiles/박세연.json`
- Create: `profiles/오유림.json`
- Create: `profiles/이하은.json`
- Create: `profiles/최유진.json`

**Interfaces:**
- Produces: five standalone profiles with ten authored events each

- [x] Author all five profiles directly, preserving each artist's distinct movement, material, color, and hair language.
- [x] Validate all five profiles for JSON structure, exact pool sizes, and local uniqueness; the project Python lacks `pytest`, so the collection suite will run through its standard-library `unittest` entry point during final verification.

### Task 4: Health, Fitness, Office, And Community Profiles

**Files:**
- Create: `profiles/박다정.json`
- Create: `profiles/서나윤.json`
- Create: `profiles/유하린.json`
- Create: `profiles/이주은.json`
- Create: `profiles/이주희.json`

**Interfaces:**
- Produces: five standalone profiles with ten authored events each

- [ ] Author all five profiles directly, balancing their professional settings with plausible off-duty styling.
- [ ] Run the collection contract test and confirm only profiles from the final task remain missing.

### Task 5: Luxury And Fashion Profiles

**Files:**
- Create: `profiles/서지수.json`
- Create: `profiles/이채영.json`
- Create: `profiles/임세라.json`

**Interfaces:**
- Produces: three standalone profiles with ten authored events each

- [ ] Author all three profiles directly with separate luxury, minimal modeling, and fashion-PR visual languages.
- [ ] Run the collection contract test and confirm all 20 profiles pass.

### Task 6: Full Verification

**Files:**
- Test: `tests/test_profiles.py`
- Verify: `profiles/*.json`

**Interfaces:**
- Consumes: all finished profiles
- Produces: evidence that the JSON-only generator supports every character

- [ ] Run `jq empty profiles/*.json` and confirm every document is valid JSON.
- [ ] Run `python3 -m unittest discover -s tests` and confirm all tests pass.
- [ ] Generate one outline per character into a temporary directory and confirm all 20 generations succeed without modifying the checked-in outline files.
