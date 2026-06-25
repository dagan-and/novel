# Wargame Turn Structure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist the new mixed-mode wargame flow in the repo so future turns use the agreed operation/tactical format instead of the old narrative-first turn structure.

**Architecture:** Keep implementation minimal and documentation-first. Preserve the current JSON state model, add the new turn protocol to the player-facing repo docs, and only introduce enough structural guidance for future manual or scripted play to follow the mixed operation/tactical loop consistently.

**Tech Stack:** Markdown documentation, existing JSON state files, Python 3 test/verification commands where needed

## Global Constraints

- Follow the approved spec in `docs/superpowers/specs/2026-06-25-wargame-turn-structure-design.md`.
- Keep the game as a `혼합형 워게임`: base flow is operation turns, tactical turns open only for decisive clashes.
- Preserve existing JSON schema unless a change is strictly required.
- Results must remain `전과표 우선, 서사 후행`.
- Avoid unrelated refactors in `generate.py` or HTML output unless the turn-flow docs require it.

---

### Task 1: Update The Primary Resume Doc For Wargame Play

**Files:**
- Modify: `RESUME.md`
- Test: manual verification in `RESUME.md`

**Interfaces:**
- Consumes: `docs/superpowers/specs/2026-06-25-wargame-turn-structure-design.md`
- Produces: a canonical player-facing resume flow that future sessions can follow without rereading the full design spec

- [ ] **Step 1: Write the expected content changes as a checklist**

```md
- Replace the old “주행동/부행동/치트키” turn format with operation-turn first instructions.
- Explain when tactical turns appear.
- Add one operation-turn input example and one tactical-turn input example.
- State that turn results must lead with front-line changes, losses, supply, and captured ground.
```

- [ ] **Step 2: Confirm the current file still contains the old format**

Run: `rg -n "주행동|부행동|치트키" RESUME.md`
Expected: matches showing the legacy turn structure still exists

- [ ] **Step 3: Update `RESUME.md` with the new mixed wargame protocol**

```md
## 턴 구조

- 기본 진행은 `작전 턴`
- 중요한 충돌이 벌어질 때만 `전술 턴`으로 확대
- 결과 보고는 `전과표 우선, 서사 후행`

### 작전 턴 입력 방식

- `주공축 1개 + 보조작전 1개 + 예비대 운용 1개 + 태세 1개`
- 예시: `1+5+8+11`

### 전술 턴 입력 방식

- `주행동 1개 + 지원행동 1개 + 리스크 규칙 1개`
- 예시: `2+6+12`
```

- [ ] **Step 4: Verify the new resume doc no longer advertises the old turn format**

Run: `rg -n "주행동|부행동|치트키" RESUME.md`
Expected: no matches for the removed legacy section, or only matches that explicitly explain it is obsolete

- [ ] **Step 5: Commit**

```bash
git add RESUME.md
git commit -m "docs: switch resume guide to wargame turn flow"
```

### Task 2: Add A Dedicated Playbook For Turn Execution

**Files:**
- Create: `docs/wargame-playbook.md`
- Test: manual verification in `docs/wargame-playbook.md`

**Interfaces:**
- Consumes: `docs/superpowers/specs/2026-06-25-wargame-turn-structure-design.md`, updated `RESUME.md`
- Produces: a compact operator playbook with copy-ready output templates for operation turns, tactical turns, and result reports

- [ ] **Step 1: Draft the playbook outline**

```md
1. Purpose
2. When to use operation turns
3. When to open tactical turns
4. Operation turn template
5. Tactical turn template
6. Result report template
7. State update checklist
```

- [ ] **Step 2: Create `docs/wargame-playbook.md` with canonical templates**

```md
# Wargame Playbook

## Operation Turn Template

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AD XX년 X분기  |  전역 작전 턴
목표: ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
...
```

## Tactical Turn Template

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AD XX년 X분기  |  전술 턴
전투 목표: ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
...
```

## Result Template

```text
[전투 결과]
- 전선 변화:
- 아군 손실:
- 적 손실 추정:
- 보급 소모:
- 확보 지형:

[전장 기록]
...
```
```

- [ ] **Step 3: Add a state-update checklist to the playbook**

```md
## State Update Checklist

- Update `events.json` with the turn title, world context, and result line
- Update `game-state.json` for front-line status, losses, supply strain, and newly held positions
- Update `tech-tree.json` only if doctrine, logistics, or medical practice actually changed
- Do not regenerate `chronicle.html` unless explicitly requested
```

- [ ] **Step 4: Verify the playbook includes all three templates**

Run: `rg -n "Operation Turn Template|Tactical Turn Template|Result Template|State Update Checklist" docs/wargame-playbook.md`
Expected: one match for each heading

- [ ] **Step 5: Commit**

```bash
git add docs/wargame-playbook.md
git commit -m "docs: add wargame turn execution playbook"
```

### Task 3: Align The Design Spec And Session Entry Point

**Files:**
- Modify: `docs/superpowers/specs/2026-06-25-wargame-turn-structure-design.md`
- Modify: `RESUME.md`
- Test: manual verification of cross-references

**Interfaces:**
- Consumes: `docs/wargame-playbook.md`
- Produces: linked documentation so a future session can find the design spec, quick-start guide, and execution templates in one path

- [ ] **Step 1: Identify where to add cross-references**

```md
- Add a short “See also” section near the top of `RESUME.md`
- Add a short “Operationalization” section near the end of the design spec
```

- [ ] **Step 2: Add cross-links between resume guide, spec, and playbook**

```md
## 관련 문서

- 빠른 진행 가이드: `RESUME.md`
- 설계 원본: `docs/superpowers/specs/2026-06-25-wargame-turn-structure-design.md`
- 진행 템플릿: `docs/wargame-playbook.md`
```

- [ ] **Step 3: Verify the links are present in both files**

Run: `rg -n "docs/wargame-playbook.md|wargame-turn-structure-design.md|관련 문서|Operationalization" RESUME.md docs/superpowers/specs/2026-06-25-wargame-turn-structure-design.md`
Expected: matches in both files showing the docs point to one another

- [ ] **Step 4: Commit**

```bash
git add RESUME.md docs/superpowers/specs/2026-06-25-wargame-turn-structure-design.md
git commit -m "docs: link wargame design and execution guides"
```

### Task 4: Verification Pass

**Files:**
- Test: `RESUME.md`, `docs/wargame-playbook.md`, `docs/superpowers/specs/2026-06-25-wargame-turn-structure-design.md`

**Interfaces:**
- Consumes: outputs of Tasks 1-3
- Produces: confidence that the new gameplay flow is documented consistently and ready for use in future turns

- [ ] **Step 1: Run document consistency checks**

Run: `rg -n "작전 턴|전술 턴|전과표 우선" RESUME.md docs/wargame-playbook.md docs/superpowers/specs/2026-06-25-wargame-turn-structure-design.md`
Expected: matches in all three files

- [ ] **Step 2: Confirm no legacy turn instructions remain in the quick-start path**

Run: `rg -n "부행동|치트키" RESUME.md docs/wargame-playbook.md`
Expected: no matches unless explicitly marked obsolete

- [ ] **Step 3: Review git diff for scope discipline**

Run: `git diff -- RESUME.md docs/wargame-playbook.md docs/superpowers/specs/2026-06-25-wargame-turn-structure-design.md`
Expected: only documentation changes related to the new wargame flow

- [ ] **Step 4: Commit**

```bash
git add RESUME.md docs/wargame-playbook.md docs/superpowers/specs/2026-06-25-wargame-turn-structure-design.md
git commit -m "docs: finalize wargame gameplay documentation"
```

## Self-Review

### Spec coverage

- Mixed-mode wargame flow: covered by Tasks 1 and 2
- Operation/tactical turn distinction: covered by Tasks 1 and 2
- Transition and result formatting: covered by Task 2
- Repo discoverability for future sessions: covered by Task 3

No uncovered spec requirement remains within the chosen documentation-first scope.

### Placeholder scan

No `TBD`, `TODO`, or undefined references remain. Commands, files, and expected outputs are explicit.

### Type consistency

This plan is documentation-only. File references and terminology are consistent: `작전 턴`, `전술 턴`, `전과표 우선`, `docs/wargame-playbook.md`.
