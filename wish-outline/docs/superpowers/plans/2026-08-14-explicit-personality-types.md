# Explicit Personality Types Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Classify every character as `강함`, `여림`, or `보통` using an explicit profile field.

**Architecture:** Store the three canonical labels in the existing keyword JSON, detect only those labels in `build_footer_text`, and map them onto the existing internal trait keys. Add one explicit personality field to each character TXT profile.

**Tech Stack:** Python 3, JSON, plain-text character profiles

## Global Constraints

- Public labels are exactly `강함`, `여림`, and `보통`.
- Internal keys remain exactly `aggressive`, `submissive`, and `default`.
- Missing or invalid metadata uses `default` and emits `성향: 보통`.
- Descriptive prose must not select a personality type.

---

### Task 1: Replace Prose Keyword Detection

**Files:**
- Modify: `tools/footer_keywords.json:493`
- Modify: `tools/append_footer.py:102`

**Interfaces:**
- Consumes: `pool["personality_type_keywords"]` and character content
- Produces: `detected_personality_type`, `trait_key`, `is_aggressive`, and `is_submissive`

- [x] **Step 1: Run a failing behavior check**

Call `build_footer_text` with `성향: 강함`, `성향: 여림`, and prose containing old keywords. Confirm the current implementation does not consistently emit the three canonical labels and still reacts to prose.

- [x] **Step 2: Add canonical configuration**

Add this top-level JSON object after `body_type_order`:

```json
"personality_type_keywords": {
  "강함": ["성향: 강함"],
  "여림": ["성향: 여림"],
  "보통": ["성향: 보통"]
}
```

- [x] **Step 3: Replace detection and preserve internal behavior**

Detect the first matching public label from `personality_type_keywords`, default to `보통`, then map it with:

```python
trait_key_by_personality_type = {
    "강함": "aggressive",
    "여림": "submissive",
    "보통": "default",
}
trait_key = trait_key_by_personality_type[detected_personality_type]
is_aggressive = trait_key == "aggressive"
is_submissive = trait_key == "submissive"
```

Replace conditional footer output with `lines.append(f"성향: {detected_personality_type}")`.

- [x] **Step 4: Verify canonical and fallback behavior**

Validate the JSON. Confirm all three explicit labels round-trip through the footer, old descriptive keywords cannot select `강함` or `여림`, and missing or invalid metadata emits `성향: 보통`.

---

### Task 2: Tag All Character Profiles

**Files:**
- Modify: `characters/*.txt`

**Interfaces:**
- Consumes: the 23 assignments in `docs/superpowers/specs/2026-08-14-explicit-personality-types-design.md`
- Produces: exactly one `- 성향: <분류명>` field in every character profile

- [x] **Step 1: Add the approved profile fields**

Insert the personality field immediately after each `- 체형:` field using these exact assignments:

```text
강함: 권은비, 서나윤, 서지수, 이하은, 임세라, 최유진, 한소희
여림: 김나영, 노은화, 도하영, 오유림, 유하린, 이주은, 이채영, 최윤서
보통: 김아영, 문아영, 박다정, 박미현, 윤수빈, 이은빈, 이주희, 차소연
```

- [x] **Step 2: Verify every profile through the real detector**

Parse all `characters/*.txt`; assert there are 23 files, each has exactly one valid body type and one valid personality type, and `build_footer_text` emits the same personality type.

- [x] **Step 3: Check the scoped diff**

Run `git diff --check -- tools/footer_keywords.json tools/append_footer.py characters` and confirm no unrelated profile content was changed.
