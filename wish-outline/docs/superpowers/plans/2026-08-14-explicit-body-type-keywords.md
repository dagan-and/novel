# Explicit Body Type Keywords Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restrict body type detection to the canonical `체형: <분류명>` field for all seven supported types.

**Architecture:** Keep the existing substring-based detector and body type priority. Simplify only its JSON keyword source so prose descriptors cannot trigger classification.

**Tech Stack:** JSON configuration, Python 3 verification

## Global Constraints

- Preserve all seven existing body type names.
- Preserve `body_type_order` and footer generation behavior.
- Do not classify descriptive prose without an explicit `체형:` field.

---

### Task 1: Simplify Body Type Keywords

**Files:**
- Modify: `tools/footer_keywords.json:468`

**Interfaces:**
- Consumes: `build_footer_text(content, pool, templates, rng)` from `tools/append_footer.py`
- Produces: `body_type_keywords` mappings with one canonical string per body type

- [x] **Step 1: Run a regression check that demonstrates the current redundant mappings**

Run a Python assertion that every `body_type_keywords` entry has exactly one item. Before the edit it must fail because each entry has six items.

- [x] **Step 2: Replace each keyword list with one canonical field string**

Use the following exact mapping:

```json
"body_type_keywords": {
  "아담": ["체형: 아담"],
  "늘씬": ["체형: 늘씬"],
  "글래머": ["체형: 글래머"],
  "근육": ["체형: 근육"],
  "육감": ["체형: 육감"],
  "저신장글래머": ["체형: 저신장글래머"],
  "빈유슬렌더": ["체형: 빈유슬렌더"]
}
```

- [x] **Step 3: Validate syntax and classification behavior**

Run `python3 -m json.tool tools/footer_keywords.json`. Then call `build_footer_text` for every explicit field and assert its corresponding `체형:` footer is present. Assert prose containing `날씬`, `골반`, `운동`, `마른`, and `긴 다리` produces no body type footer.

- [x] **Step 4: Review the scoped diff**

Run `git diff --check -- tools/footer_keywords.json` and inspect the `body_type_keywords` block to confirm `body_type_order` is unchanged.
