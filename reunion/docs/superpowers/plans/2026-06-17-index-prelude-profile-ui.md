# Index Prelude Profile UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update generated HTML so the index keeps episode links visible while stacking three vertical utility buttons, the prelude gallery removes its title area, and profile adult-scene text becomes compact heart-plus-count copy.

**Architecture:** Adjust the HTML generators rather than hand-editing output so future publishes stay consistent. Cover each requested display change with regression tests, then regenerate the affected HTML files.

**Tech Stack:** Python, unittest, generated static HTML

## Global Constraints

- Keep changes inside the existing generator scripts and generated HTML outputs.
- Follow TDD: add or update failing tests before modifying production code.
- Preserve existing visual language unless the user explicitly requested a layout/text change.

---

### Task 1: Lock expected UI behavior in tests

**Files:**
- Modify: `tests/test_convert_setting.py`
- Modify: `tests/test_convert_profiles.py`
- Create or Modify: `tests/test_convert_preludes.py`

**Interfaces:**
- Consumes: `python3 convert_setting.py`, `python3 convert_profiles.py`, `python3 convert_preludes.py`
- Produces: regression coverage for index layout, prelude title removal, and profile adult-scene copy

- [ ] Add assertions for episode links plus a vertical utility button container in `html/index.html`.
- [ ] Update profile assertions to expect `♥ {count}` style output and no `성인씬` label/count copy.
- [ ] Add a prelude-page test asserting the top `삽화` title block is absent while the gallery remains.

### Task 2: Update generators to satisfy the new UI

**Files:**
- Modify: `convert_setting.py`
- Modify: `convert_profiles.py`
- Modify: `convert_preludes.py`

**Interfaces:**
- Consumes: current generator inputs and test expectations
- Produces: regenerated `html/index.html`, `html/characters/*.html`, `html/preludes.html`

- [ ] Change the index generator CSS/markup so episode groups render and the three utility buttons stack vertically.
- [ ] Remove the prelude page title area from the generator template.
- [ ] Replace profile adult-scene label/count text with a compact `♥ {count}` display.

### Task 3: Regenerate outputs and verify

**Files:**
- Modify: `html/index.html`
- Modify: `html/preludes.html`
- Modify: `html/characters/*.html`

**Interfaces:**
- Consumes: updated generators
- Produces: checked-in generated HTML matching the new templates

- [ ] Run the focused test suite until green.
- [ ] Regenerate the affected HTML outputs with the project scripts.
- [ ] Re-run the same tests after regeneration to confirm the checked-in files match generator behavior.
