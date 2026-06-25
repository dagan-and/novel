# Baekje HTML Chronicle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compact turn data should generate a Korean HTML chronicle with dramatic turn-by-turn navigation.

**Architecture:** Store minimal turn records in a JSON file and render a single static HTML document from a Python generator. Keep the renderer small, deterministic, and testable so future turns only require appending JSON entries and re-running generation.

**Tech Stack:** Python 3, JSON, static HTML/CSS/JavaScript, unittest

## Global Constraints

- Data must stay compact and structured for long-running campaigns.
- Display copy must be Korean and read like a dramatic war briefing.
- Navigation must work inside one HTML file with previous/next controls.
- No external dependencies or frameworks.

---

### Task 1: Add generator tests first

**Files:**
- Create: `baekje-world-conquest/tests/test_generate.py`
- Test: `baekje-world-conquest/tests/test_generate.py`

**Interfaces:**
- Consumes: `generate.load_turns(path: Path) -> list[dict]`, `generate.generate_html(turns: list[dict]) -> str`
- Produces: coverage for compact JSON loading and Korean HTML rendering

- [ ] **Step 1: Write the failing test**

```python
import json
import tempfile
import unittest
from pathlib import Path

import generate


class LoadTurnsTests(unittest.TestCase):
    def test_load_turns_reads_compact_turn_data(self):
        sample = [{"turn": 1, "year": "기원후 12년", "codename": "정리", "headline": "시험", "summary": "요약", "actions": [], "outcome": "결과", "state_changes": [], "risks": []}]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "turns.json"
            path.write_text(json.dumps(sample, ensure_ascii=False), encoding="utf-8")

            turns = generate.load_turns(path)

        self.assertEqual(turns[0]["codename"], "정리")


class HtmlRenderTests(unittest.TestCase):
    def test_generate_html_renders_korean_turn_navigation(self):
        turns = [{"turn": 1, "year": "기원후 12년", "codename": "정리", "headline": "백제가 숨을 고른다", "summary": "전황 브리핑", "actions": ["창고 재조사"], "outcome": "군량 회복", "state_changes": ["보급 안정"], "risks": ["귀족 반발"]}]

        html = generate.generate_html(turns)

        self.assertIn("전황 브리핑", html)
        self.assertIn("다음 턴", html)
        self.assertIn("백제가 숨을 고른다", html)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest baekje-world-conquest/tests/test_generate.py -v`
Expected: FAIL because `generate.py` and required functions do not exist yet

- [ ] **Step 3: Write minimal implementation**

```python
def load_turns(path):
    ...


def generate_html(turns):
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest baekje-world-conquest/tests/test_generate.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add baekje-world-conquest/tests/test_generate.py baekje-world-conquest/generate.py
git commit -m "feat: add baekje html chronicle generator"
```

### Task 2: Add compact turn data and output target

**Files:**
- Create: `baekje-world-conquest/turns.json`
- Modify: `baekje-world-conquest/README.md`

**Interfaces:**
- Consumes: compact turn schema from the design doc
- Produces: canonical data source for HTML generation

- [ ] **Step 1: Write the failing test**

```python
class LoadRealTurnsTests(unittest.TestCase):
    def test_real_turn_data_contains_multiple_turns(self):
        turns = generate.load_turns(generate.BASE / "turns.json")
        self.assertGreaterEqual(len(turns), 10)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest baekje-world-conquest/tests/test_generate.py -v`
Expected: FAIL because `turns.json` does not exist yet

- [ ] **Step 3: Write minimal implementation**

```json
[
  {
    "turn": 1,
    "year": "기원후 12년",
    "codename": "제1차 정리",
    "headline": "백제는 정복을 멈추고 국가를 다시 세기 시작했다.",
    "summary": "..."
  }
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest baekje-world-conquest/tests/test_generate.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add baekje-world-conquest/turns.json baekje-world-conquest/README.md
git commit -m "feat: add compact baekje turn data"
```

### Task 3: Generate the navigable HTML chronicle

**Files:**
- Modify: `baekje-world-conquest/generate.py`
- Create: `baekje-world-conquest/chronicle.html`

**Interfaces:**
- Consumes: `load_turns(path)` and `generate_html(turns)`
- Produces: `write_html(turns, destination)` and browser-ready `chronicle.html`

- [ ] **Step 1: Write the failing test**

```python
class WriteHtmlTests(unittest.TestCase):
    def test_write_html_creates_a_turn_by_turn_chronicle_file(self):
        turns = [{"turn": 1, "year": "기원후 12년", "codename": "정리", "headline": "시험", "summary": "요약", "actions": [], "outcome": "결과", "state_changes": [], "risks": []}]
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "chronicle.html"

            generate.write_html(turns, target)

            self.assertTrue(target.exists())
            self.assertIn("이전 턴", target.read_text(encoding="utf-8"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest baekje-world-conquest/tests/test_generate.py -v`
Expected: FAIL because `write_html` does not exist yet

- [ ] **Step 3: Write minimal implementation**

```python
def write_html(turns, destination):
    destination.write_text(generate_html(turns), encoding="utf-8")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest baekje-world-conquest/tests/test_generate.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add baekje-world-conquest/generate.py baekje-world-conquest/chronicle.html
git commit -m "feat: render baekje html chronicle"
```
