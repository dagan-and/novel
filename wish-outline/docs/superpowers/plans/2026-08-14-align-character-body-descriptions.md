# Align Character Body Descriptions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make five character body descriptions agree with their explicit body type metadata.

**Architecture:** Edit only body-related metadata and prose in the existing TXT profiles. Preserve all personality metadata and prose, relationships, speech, appearance details outside the body paragraph, and scene hooks.

**Tech Stack:** Plain-text character profiles, Python 3 verification

## Global Constraints

- Keep every existing `체형` and `성향` tag unchanged.
- Keep all character heights unchanged.
- Set 박다정 to `50kg`, 박미현 to `45kg`, and 차소연 to `52kg`.
- Do not edit any personality section.

---

### Task 1: Align Five Body Profiles

**Files:**
- Modify: `characters/김아영.txt`
- Modify: `characters/박다정.txt`
- Modify: `characters/박미현.txt`
- Modify: `characters/임세라.txt`
- Modify: `characters/차소연.txt`

**Interfaces:**
- Consumes: existing `체형` metadata in each profile
- Produces: matching height/weight metadata, body paragraph, and body summary sentence

- [x] **Step 1: Record the current contradictory phrases**

Assert that the files currently contain the old phrases `가슴은 너무 작지 않은`, `빈유슬렌더에 가까운`, `포동한 온기`, `글래머라는 말이`, and `글래머한 과시보다`.

- [x] **Step 2: Apply the approved body-only rewrites**

Use these exact directions:

```text
김아영: 155cm/42kg 유지, 작은 가슴과 좁은 골격의 빈유슬렌더로 수정
박다정: 160cm/50kg, 부드러운 가슴·허리·골반·허벅지의 절제된 육감형으로 수정
박미현: 156cm/45kg, 가는 어깨·허리·팔다리와 정돈된 세로선의 늘씬형으로 수정
임세라: 161cm/49kg 유지, 볼륨보다 길고 슬림한 선과 옷태 중심으로 수정
차소연: 162cm/52kg, 가슴·허리·골반·허벅지 대비가 분명한 균형 잡힌 글래머로 수정
```

- [x] **Step 3: Verify metadata and prose alignment**

Assert all five files retain one body tag and one personality tag, the three changed weights match the approved values, and each body paragraph contains its canonical body type name.

- [x] **Step 4: Verify removal and scope**

Assert the five contradictory phrases are absent. Run `git diff --check` on the five files and inspect the edited body blocks.
