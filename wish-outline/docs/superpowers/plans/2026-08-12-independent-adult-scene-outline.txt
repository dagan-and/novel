# Independent Adult Scene Outline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Change the repository guidance so future outline work treats each request as an independent adult scene outline rather than a continuous episode.

**Architecture:** Add one new core rule file as the primary source of truth, then update repository entry points to reference it first. Existing character and world files remain optional reference material.

**Tech Stack:** Markdown/plain text repository guidance.

## Global Constraints

- Do not delete existing reference material.
- Keep the new workflow independent from previous episode continuity by default.
- Maintain the rule that all sexual situations involve adults with clear mutual consent.
- Avoid graphic prose; keep output at outline and scene-direction level.

---

### Task 1: Add New Core Rule File

**Files:**
- Create: `00_core/성인씬_개요_작성_기준.txt`

**Interfaces:**
- Consumes: Current repository structure and existing adult-scene reference file.
- Produces: Primary guidance file for independent adult scene outlines.

- [ ] **Step 1: Create the file**

Write a concise rule document that defines the new default: independent adult scene outline generation with no continuity obligation.

- [ ] **Step 2: Verify scope**

Run: `rg "개요_작성_기본파일|성인씬_개요_작성_기준|상태 파일|상태 갱신" AGENTS.md CLAUDE.md 00_INDEX.txt 00_core`

Expected: references point to the new guidance file and no entry point still requires the deleted old file.

### Task 2: Update Repository Entry Points

**Files:**
- Modify: `AGENTS.md`
- Modify: `CLAUDE.md`
- Modify: `00_INDEX.txt`

**Interfaces:**
- Consumes: `00_core/성인씬_개요_작성_기준.txt`
- Produces: Updated top-level instructions for future agents.

- [ ] **Step 1: Replace old priority file references**

Change references from `00_core/개요_작성_기본파일.txt` to `00_core/성인씬_개요_작성_기준.txt`.

- [ ] **Step 2: Remove automatic continuity maintenance**

Make state/tracking/outline files optional references only when the user requests continuity or a named character requires consistency.

- [ ] **Step 3: Verify**

Run: `rg "개요_작성_기본파일|새 개요를 확정|관련 상태 파일도 함께 갱신|61화 이후" AGENTS.md CLAUDE.md 00_INDEX.txt`

Expected: no old mandatory workflow remains.
