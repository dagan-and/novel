# HTML Title, Origin, Long-Term Plan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the shared work-title text from generated HTML, add per-character origin fields, and wire a long-term planning file into the novel workflow.

**Architecture:** Update the Python HTML generators so page titles and visible headers stop injecting the shared series name while preserving per-page navigation and structure. Extend character source markdown with a dedicated `출신` field, ensure profile HTML renders it naturally, and connect a new planning markdown file through the workflow docs so future `소설 진행해줘` runs can reference it.

**Tech Stack:** Python 3, unittest, Markdown source files, existing repository HTML converters

## Global Constraints

- Keep edits aligned with the repository workflow files under `setting/`.
- Preserve existing HTML generation flow and file paths.
- Add behavior through TDD: write failing tests first, then minimal implementation.

---

### Task 1: Lock the new HTML/output expectations with tests

**Files:**
- Modify: `tests/test_convert_profiles.py`
- Modify: `tests/test_convert_html.py`

**Interfaces:**
- Consumes: `python3 convert_profiles.py <name>`, `python3 convert_html.py <episode>`
- Produces: Regression coverage for title removal and origin rendering

- [ ] **Step 1: Write the failing tests**
- [ ] **Step 2: Run the targeted tests and confirm they fail for the new expectations**
- [ ] **Step 3: Keep the failures focused on missing behavior, not test setup**

### Task 2: Update generators and source data

**Files:**
- Modify: `convert_html.py`
- Modify: `convert_profiles.py`
- Modify: `convert_setting.py`
- Modify: `convert_preludes.py`
- Modify: `characters/캐릭터양식.md`
- Modify: `characters/이하은.md`
- Modify: `characters/임소율.md`
- Modify: `characters/한서진.md`
- Modify: `characters/정다온.md`
- Modify: `characters/박미현.md`
- Modify: `characters/오연서.md`
- Modify: `characters/배수인.md`
- Add: `setting/장기연재계획.md`
- Modify: `setting/워크플로우.md`
- Modify: `setting/개요작성규칙.md`

**Interfaces:**
- Consumes: Existing markdown schema and HTML generator templates
- Produces: Title-free generated HTML, character markdown with `출신`, workflow docs that reference the new planning file

- [ ] **Step 1: Remove shared work-title text from generated HTML titles and visible top headings where applicable**
- [ ] **Step 2: Add `출신` to the character template and existing character files**
- [ ] **Step 3: Create `setting/장기연재계획.md` as the canonical long-term plan file**
- [ ] **Step 4: Connect that file from workflow/outline-reference docs**

### Task 3: Verify generators end to end

**Files:**
- Reuse modified files from Tasks 1-2

**Interfaces:**
- Consumes: Updated tests and generators
- Produces: Fresh verification evidence for the completed behavior

- [ ] **Step 1: Run the targeted regression tests**
- [ ] **Step 2: Regenerate affected HTML outputs**
- [ ] **Step 3: Run the full relevant test subset and confirm clean exits**
