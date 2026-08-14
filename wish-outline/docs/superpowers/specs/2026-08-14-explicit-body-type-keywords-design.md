# Explicit Body Type Keywords

## Goal

Infer a character's body type only from an explicit `체형: <분류명>` field. Descriptive prose must not affect classification.

## Configuration

Keep the existing seven body type names and `body_type_order`. Each entry in `body_type_keywords` contains only its canonical field value, such as `체형: 늘씬`.

## Behavior

- `- 체형: 늘씬` is classified as `늘씬` because the canonical field text is present.
- Descriptions such as `날씬`, `골반`, `운동`, or `마른` do not select a body type.
- Existing footer generation and type-specific instruction selection remain unchanged.

## Verification

Validate the JSON, confirm every type has exactly one canonical keyword, and test that explicit fields match while descriptive prose does not.
