# Explicit Personality Types

## Goal

Classify character personality from one explicit profile field instead of searching descriptive prose for overlapping keywords.

## Profile Format

Every file in `characters/` contains exactly one of these fields immediately after its body type field:

```text
- 성향: 강함
- 성향: 여림
- 성향: 보통
```

Assignments:

- 강함: 권은비, 서나윤, 서지수, 이하은, 임세라, 최유진, 한소희
- 여림: 김나영, 노은화, 도하영, 오유림, 유하린, 이주은, 이채영, 최윤서
- 보통: 김아영, 문아영, 박다정, 박미현, 윤수빈, 이은빈, 이주희, 차소연

## Detection And Mapping

Add `personality_type_keywords` to `tools/footer_keywords.json`, with one canonical keyword per type: `성향: 강함`, `성향: 여림`, and `성향: 보통`.

Replace prose keyword counting in `tools/append_footer.py` with explicit personality detection. Map public labels to the existing internal trait keys:

- `강함` maps to `aggressive`.
- `여림` maps to `submissive`.
- `보통` maps to `default`.
- Missing or invalid metadata falls back to `default` for compatibility with inputs that do not contain a character profile.

Existing trait template selection, force-level weighting, and male-response selection continue using the internal keys.

## Footer Output

Always emit the selected public label as `성향: 강함`, `성향: 여림`, or `성향: 보통`. Inputs without a valid personality field emit `성향: 보통` because they use the compatibility fallback.

## Verification

- Validate the JSON configuration.
- Confirm all 23 character files contain exactly one valid body type and one valid personality type.
- Confirm every character produces the expected personality footer.
- Confirm descriptive prose alone cannot select `강함` or `여림`.
- Confirm missing or invalid personality metadata produces `성향: 보통` and uses the `default` behavior branch.
