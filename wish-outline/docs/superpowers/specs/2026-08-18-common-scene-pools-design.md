# Common Scene Pools Design

## Goal

Generate outlines without character-specific JSON profiles. Keep all reusable
scene configuration in `profiles/common_arcs.json`, while character identity,
body type, personality, and prose remain in `characters/<name>.txt`.

## Common Configuration

`profiles/common_arcs.json` retains its existing `arcs` list and adds three
top-level fields:

- `scene_type_weights`: `work` is 60 and `indoor` is 40.
- `locations`: separate `work` and `indoor` location lists.
- `outfits`: common outfit pools keyed by body type and then scene type.

The supported body types are the values already used by character files:
`아담`, `늘씬`, `글래머`, `근육`, `육감`, `저신장글래머`, and
`빈유슬렌더`.

Work locations are:

- 퇴근 후 호텔
- 비상계단
- 사옥 옥상
- 건물 화장실

Indoor locations are:

- 호텔 객실
- 실내 수영장
- 호텔 욕실

Each location contains an ID, display name, weather/atmosphere choices,
pressure text, and place-detail choices. No location contains a uniform or a
character-specific restriction.

Each body type has `work` and `indoor` outfit lists. Work outfits are general
office or after-work clothing, not profession-specific uniforms. Indoor
outfits are general hotel, pool, or private indoor clothing suited to that
body type.

## Selection Flow

1. Load all character text files. A character no longer needs a matching JSON
   profile.
2. Read `리부트 포지션`, `체형`, and `성향` from the character text.
3. Select `work` or `indoor` with weights 60:40.
4. Select one location from the chosen scene type.
5. Select one outfit from the character body type and chosen scene type.
6. Select an existing common arc using the current episode/character-based
   arc selection.
7. Render the outline with the selected location, outfit, and arc.

The character's own hair description remains authoritative. The generated
scene instructs the writer/image model to preserve the hairstyle from the
character profile instead of selecting hair from a removed character JSON.

## Validation And Errors

The common configuration loader validates all required top-level fields,
weights, location fields, supported body-type outfit pools, and non-empty
lists. Missing or invalid common data raises a clear `ValueError` before any
outline is written.

A character with a missing or unsupported `체형` also raises a clear
`ValueError`. There is no silent body-type fallback because that could assign
an unsuitable outfit.

## Compatibility

`common_arcs.json` remains the only file used for common arc loading. Existing
arc entries and deterministic arc selection are preserved. The removed
character JSON files are no longer consulted by generation or character
filtering.

`python3 generate_outlines.py <count>` and `python3 run_pipeline.py <count>`
keep their current command-line interfaces.

## Testing

Tests cover:

- loading and validating the expanded common configuration;
- generating with character text files when no character JSON exists;
- enforcing the 60:40 scene-type weights through an injected random source;
- selecting outfits from the matching body type and scene type;
- preserving the existing common arc fields in generated scenes;
- rejecting missing body types and malformed common configuration.
