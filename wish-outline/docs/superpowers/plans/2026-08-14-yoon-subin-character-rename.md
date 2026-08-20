# 윤수빈 Character Rename Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 기존 캐릭터를 윤수빈으로 리네임하고 외형/관계 캐논을 동기화한다.

**Architecture:** The repository stores character canon in `characters/*.txt`, generation data in `profiles/*.json`, and generated scene outlines in `outlines/*.txt`. This change updates the canonical character file first, then mechanically syncs profile and outline references.

**Tech Stack:** Markdown/text files, JSON profiles, shell validation with `rg` and `python3 -m json.tool`.

## Global Constraints

- Do not change unrelated dirty worktree files.
- Keep edits limited to 기존 이름/윤수빈 references and directly embedded profile text.
- Preserve existing outline structure and footer metadata.

---

### Task 1: Canonical Character File

**Files:**
- Rename: `characters/<기존이름>.txt` to `characters/윤수빈.txt`
- Modify: `characters/윤수빈.txt`

**Interfaces:**
- Consumes: user-provided external appearance and relationship brief.
- Produces: the canonical markdown block embedded in existing outlines.

- [ ] **Step 1: Rename the file**

Run: `mv characters/<기존이름>.txt characters/윤수빈.txt`

- [ ] **Step 2: Replace the character body**

Set the title, name references, appearance, and relationship so the file uses 윤수빈/수빈 throughout.

- [ ] **Step 3: Verify old name is gone from the canonical file**

Run: `rg "<old-name>|<old-short-name>|<old-id>" characters/윤수빈.txt`
Expected: no matches.

### Task 2: Profile JSON Rename

**Files:**
- Rename: `profiles/김민정.json` to `profiles/윤수빈.json`
- Modify: `profiles/윤수빈.json`

**Interfaces:**
- Consumes: profile event ids and prompt pools.
- Produces: valid JSON with 윤수빈/수빈/subin identifiers.

- [ ] **Step 1: Rename the file**

Run: `mv profiles/김민정.json profiles/윤수빈.json`

- [ ] **Step 2: Replace names and ids**

Replace the old full name with `윤수빈`, old short name with `수빈`, and old romanized id with `subin`.

- [ ] **Step 3: Validate JSON**

Run: `python3 -m json.tool profiles/윤수빈.json >/tmp/yoon-subin-profile.json`
Expected: exit code 0.

### Task 3: Prompt And Outline Sync

**Files:**
- Modify: `prompts/outline.txt`
- Modify: `outlines/011화.txt`
- Modify: `outlines/026화.txt`
- Modify: `outlines/060화.txt`
- Modify: `outlines/064화.txt`
- Modify: `outlines/088화.txt`

**Interfaces:**
- Consumes: the canonical `characters/윤수빈.txt` body.
- Produces: outline files with matching name, relationship, and embedded profile block.

- [ ] **Step 1: Replace simple references**

Replace the old full name with `윤수빈`, old short name with `수빈`, and old romanized id with `subin` in the listed prompt/outline files.

- [ ] **Step 2: Refresh embedded profile blocks**

Replace each outline's embedded character profile block between `# 윤수빈` and `시기:` with the full content of `characters/윤수빈.txt`.

- [ ] **Step 3: Search for stale references**

Run: `rg "<old-name>|<old-short-name>|<old-id>" characters profiles prompts outlines docs/superpowers/specs/2026-08-14-yoon-subin-character-rename-design.md docs/superpowers/plans/2026-08-14-yoon-subin-character-rename.md`
Expected: no stale references outside historical docs that intentionally describe the change.
