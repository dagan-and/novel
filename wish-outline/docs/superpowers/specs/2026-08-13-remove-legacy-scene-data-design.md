# Remove Legacy Scene Data Design

## Goal

Make JSON profiles the only source of character-specific scene data and remove
the unused built-in scene pools from `generate_outlines.py`.

## Retained Data Flow

The generator loads character description text from `characters/<name>.txt`,
event and styling data from `profiles/<name>.json`, and narrative arc data from
`profiles/common_arcs.json`.

For every episode, `select_scene()` selects one profile event, one outfit from
that event, one hairstyle from that event, and one common arc. It does not
contain a fallback path for characters without JSON profiles.

## Removed Code

Delete `SCENE_SETS`, `CHARACTER_GROUPS`, `LUXURY_HOTEL_LOCATIONS`,
`LOCATION_POOLS`, `OUTFIT_POOLS`, and `HAIR_VARIANTS`.

Delete the helper functions `hair_kind()` and `outfit_group()`. Simplify
`event_place_details()` so it reads only `event["place_details"]`, removing the
legacy `place_rules.must_include` compatibility path.

Delete the non-profile branch in `select_scene()` and remove the unused `group`
field from returned scene dictionaries.

## Error Handling

The existing command-line filtering continues to reject characters without a
matching JSON profile. If `select_scene()` is called directly for such a
character, it raises a clear `ValueError` naming the missing character profile.

Malformed profile event data is not silently replaced by built-in defaults.
Missing required fields surface as generation errors so the profile can be
fixed at its source.

## Tests

- A JSON-profiled character still selects its place, atmosphere, outfit, and
  hairstyle from its event.
- Direct scene selection rejects a character without a JSON profile.
- Profile events use `place_details` and contain no legacy `place_rules`.
- Scene results no longer include `group`.
- The full test suite and a sample 윤수빈 outline generation pass after removal.
