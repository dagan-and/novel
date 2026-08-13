# Common Arcs JSON Design

## Goal

Move shared scene arcs out of `generate_outlines.py` into one JSON file so every
character event can combine its place and styling data with an independently
managed common arc.

## Data File

Store the shared data at `profiles/common_arcs.json` with this shape:

```json
{
  "arcs": [
    {
      "type": "male_b",
      "start": "남자가 인사한다.",
      "turn": "'여기서 이러면...' 하고 작게 중얼거린다.",
      "after": "귀에 대고 속삭인다."
    }
  ]
}
```

Each arc must contain non-empty string values for `type`, `start`, `turn`, and
`after`. The `type` field is metadata only. It does not filter or weight arc
selection.

## Loading And Validation

The `profiles` package exposes a dedicated common-arc loader. It reads
`profiles/common_arcs.json`, verifies that `arcs` is a non-empty list, and
validates every required field.

A missing file, invalid JSON, empty list, malformed arc, or blank required value
stops generation with a clear error. There is no silent fallback to hard-coded
arcs because the JSON file is the single source of truth.

## Selection And Composition

The generator loads the common arcs independently from character profiles.
After it selects an event, outfit, and hairstyle, it selects one arc from the
entire common list using the existing deterministic `pick` calculation.

Selection does not inspect `type`. The same episode and character produce the
same arc on repeated runs as long as the arc list and its ordering remain the
same. Different episodes distribute selections across the list rather than
using nondeterministic runtime randomness.

The selected arc supplies `start`, `turn`, and `after`. Its `type` is also added
to the scene result as `arc_type` so downstream output or future selection rules
can use it without changing the JSON contract.

Character event objects remain free of `arcs`. The event JSON continues to own
place, atmosphere, outfit, hair, and exposure styling only.

## Compatibility

Remove the built-in `SCENE_ARCS` constant. Both profile-backed scene selection
and the legacy non-profile branch use the common JSON loader, ensuring one arc
source for all generation paths.

`common_arcs.json` is not treated as a character profile because character
profiles are loaded by exact character filename.

## Tests

- The common-arc loader returns the JSON arcs and preserves `type`.
- Missing, empty, and malformed common-arc data raises a clear validation error.
- Profile events do not contain local `arcs`.
- Scene selection uses an entry from the common JSON file.
- `type` does not filter selection and is exposed as `arc_type`.
- Repeating the same episode and character produces the same selected arc.
- The full test suite and a sample outline generation command pass.
