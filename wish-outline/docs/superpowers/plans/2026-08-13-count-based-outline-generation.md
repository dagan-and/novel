# Count-based Outline Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate exactly the requested episode range using only JSON-profiled characters by default.

**Architecture:** Add a small argparse-based command interface and extract profile filtering plus file generation into testable functions in `generate_outlines.py`. Preserve the existing scene selection and rendering functions, and keep files beyond the requested range untouched.

**Tech Stack:** Python 3 standard library (`argparse`, `pathlib`, `unittest`, `tempfile`)

## Global Constraints

- `python3 generate_outlines.py 10` writes `001화.txt` through `010화.txt`.
- The count must be a positive integer.
- The default character pool contains only characters with `profiles/<name>.json`.
- `--character <name>` requires both the character text file and JSON profile.
- Existing files after the requested range are preserved.
- Existing scene selection and outline rendering behavior remains unchanged.

---

### Task 1: Requested Count and Profile-backed Character Pool

**Files:**
- Modify: `generate_outlines.py:1-12,633-650`
- Test: `tests/test_profiles.py`

**Interfaces:**
- Consumes: `load_characters() -> list[Character]`, `get_profile(name: str) -> dict | None`
- Produces: `positive_count(value: str) -> int`, `parse_args(argv: list[str]) -> argparse.Namespace`, `profiled_characters(characters: list[Character], character_name: str | None = None) -> list[Character]`

- [ ] **Step 1: Write failing argument and character-pool tests**

```python
def test_parse_args_accepts_requested_count_and_character(self):
    module = load_generator()
    args = module.parse_args(["10", "--character", "김민정"])
    self.assertEqual(args.count, 10)
    self.assertEqual(args.character, "김민정")

def test_parse_args_rejects_non_positive_count(self):
    module = load_generator()
    with self.assertRaises(SystemExit):
        module.parse_args(["0"])

def test_profiled_characters_uses_only_json_profiles(self):
    module = load_generator()
    characters = module.profiled_characters(module.load_characters())
    self.assertEqual([character.name for character in characters], ["김민정"])

def test_profiled_characters_rejects_character_without_json(self):
    module = load_generator()
    with self.assertRaisesRegex(ValueError, "JSON profile"):
        module.profiled_characters(module.load_characters(), "노은화")
```

- [ ] **Step 2: Run tests and verify the new API is missing**

Run: `python3 -m unittest tests.test_profiles`

Expected: FAIL because `parse_args` and `profiled_characters` do not exist.

- [ ] **Step 3: Implement count parsing and profile filtering**

```python
import argparse

def positive_count(value: str) -> int:
    count = int(value)
    if count < 1:
        raise argparse.ArgumentTypeError("count must be a positive integer")
    return count

def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate profile-backed outline files.")
    parser.add_argument("count", type=positive_count)
    parser.add_argument("--character")
    return parser.parse_args(argv)

def profiled_characters(
    characters: list[Character],
    character_name: str | None = None,
) -> list[Character]:
    available = [character for character in characters if get_profile(character.name)]
    if character_name is None:
        if not available:
            raise ValueError("no character JSON profiles found")
        return available
    selected = [character for character in available if character.name == character_name]
    if not selected:
        raise ValueError(f"character JSON profile not found: {character_name}")
    return selected
```

- [ ] **Step 4: Run focused tests**

Run: `python3 -m unittest tests.test_profiles`

Expected: PASS.

### Task 2: Generate Only the Requested Range

**Files:**
- Modify: `generate_outlines.py:738-750`
- Test: `tests/test_profiles.py`
- Modify: `prompts/outline.txt:18-25`

**Interfaces:**
- Consumes: `profiled_characters(...)`, `select_scene(ep, char)`, `outline_text(ep, char, scene)`
- Produces: `generate_outlines(count: int, character_name: str | None = None, output_dir: Path = OUTLINE_DIR) -> list[Path]`, `main(argv: list[str] | None = None) -> int`

- [ ] **Step 1: Write a failing filesystem behavior test**

```python
def test_generate_outlines_writes_requested_count_with_only_profiled_character(self):
    module = load_generator()
    with tempfile.TemporaryDirectory() as temporary_directory:
        output_dir = Path(temporary_directory)
        later_file = output_dir / "011화.txt"
        later_file.write_text("keep", encoding="utf-8")

        written = module.generate_outlines(3, output_dir=output_dir)

        self.assertEqual([path.name for path in written], ["001화.txt", "002화.txt", "003화.txt"])
        self.assertFalse((output_dir / "004화.txt").exists())
        self.assertEqual(later_file.read_text(encoding="utf-8"), "keep")
        for path in written:
            self.assertIn("- 김민정", path.read_text(encoding="utf-8"))
```

- [ ] **Step 2: Run the test and verify generation API is missing**

Run: `python3 -m unittest tests.test_profiles.CharacterProfileTests.test_generate_outlines_writes_requested_count_with_only_profiled_character`

Expected: FAIL because `generate_outlines` does not exist.

- [ ] **Step 3: Implement requested-range generation and CLI main**

```python
def generate_outlines(
    count: int,
    character_name: str | None = None,
    output_dir: Path = OUTLINE_DIR,
) -> list[Path]:
    characters = profiled_characters(load_characters(), character_name)
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for ep in range(1, count + 1):
        char = characters[(ep - 1) % len(characters)]
        scene = select_scene(ep, char)
        path = output_dir / f"{ep:03d}화.txt"
        path.write_text(outline_text(ep, char, scene), encoding="utf-8")
        written.append(path)
    return written

def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    try:
        written = generate_outlines(args.count, args.character)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    print(f"Generated {len(written)} outline files: {written[0].name} - {written[-1].name}.")
    return 0
```

- [ ] **Step 4: Update the operating prompt command examples**

```markdown
python3 generate_outlines.py 10
python3 generate_outlines.py 10 --character 김민정
```

Document that only JSON-profiled characters are selected by default and later existing files are preserved.

- [ ] **Step 5: Run the full test suite**

Run: `python3 -m unittest discover -s tests`

Expected: all tests PASS.

- [ ] **Step 6: Verify the real command without touching existing output**

Run in a temporary directory through the Python API and verify exactly three paths are returned, each uses 김민정, and a pre-existing later file remains unchanged.

- [ ] **Step 7: Commit implementation**

```bash
git add wish-outline/generate_outlines.py wish-outline/tests/test_profiles.py wish-outline/prompts/outline.txt wish-outline/docs/superpowers/plans/2026-08-13-count-based-outline-generation.md
git commit -m "Add count-based outline generation"
```
