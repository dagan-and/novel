# Hand-Authored Character Profiles Design

## Goal

Create complete JSON profiles for the remaining 19 adult characters, with each
character's ten requested places and individually authored styling that reflects
her personality, occupation, appearance, body proportions, and established hair.

## Authoring Method

Every profile is written directly as a finished JSON document. No profile
builder, shared styling template, runtime outfit generator, or mechanical phrase
combiner is introduced.

The character files under `characters/` are the creative source for personality,
speech, occupation, physical proportions, hair color, hair length, and signature
visual behavior. The supplied place list is authoritative and remains in the
given order.

The two places shared by every character, `고급호텔 스위트룸` and
`고급호텔 실내 수영장`, receive character-specific treatments. Their outfits,
hair, makeup, accessories, atmosphere, and exposure focus are not copied between
characters.

## Profile Schema

Each file at `profiles/<character>.json` has the same structure as the existing
김민정 profile:

```json
{
  "name": "캐릭터명",
  "events": [
    {
      "id": "stable_unique_id",
      "place": "장소",
      "weather": "장소의 시간과 공기",
      "pressure": "장면의 현실적인 긴장",
      "place_details": ["구체적인 공간 요소"],
      "exposure_focus": "이 장소의 주된 노출 포인트",
      "outfit_pool": ["직접 작성한 스타일링 10종"],
      "hair_pool": ["직접 작성한 헤어 5종"]
    }
  ]
}
```

Profiles contain no local `arcs`. Narrative arcs continue to come only from
`profiles/common_arcs.json`.

## Styling Rules

Each event contains exactly ten complete styling descriptions. Every description
combines an outfit with location-appropriate makeup, shoes, accessories, fabric,
fit, and a clear but realistic exposure decision.

Exposure emphasis rotates across the ten places: neckline and collarbone, back
and shoulders, waist and abdomen, thigh and leg line, and close-fitting silhouette.
It does not rely on reducing fabric area alone. Necklines, slits, backless cuts,
off-shoulder shapes, halter shapes, crop proportions, sheer layering, sheen, and
fabric movement are used only where the place can plausibly support them.

Each event contains exactly five hairstyles derived from the character's
established length and color. Variations may include tied, half-up, upstyle,
loosely disordered, rain-damp, pool-wet, or naturally released forms, but may not
contradict the base haircut. A short bob is never silently turned into long hair,
and a restrained character's styling remains distinct from a flamboyant one.

All 19 characters are adults in the 2026 setting. Styling remains mature and
sensual without depicting explicit sexual acts.

## Character Differentiation

Every outfit description names at least one body characteristic established in
the character file and explains how the garment's cut, fit, weight, or exposure
interacts with it. Body language stays exact: generic glamour traits such as
long legs, a tall silhouette, or an extremely narrow waist may not replace the
source profile's compact proportions, straight legs, soft volume, athletic
density, or other distinct build.

Styling also carries character behavior through posture, habitual movement,
professional self-presentation, guardedness, confidence, or the contrast between
public and private appearance. A sentence that remains plausible after replacing
only the character name is not sufficiently authored and must be rewritten.

Every character receives her own material palette, color range, makeup intensity,
shoe language, accessory scale, and relationship to formality. Examples include
노은화's attempted maturity over lively small-scale details, 박다정's clean and
controlled minimalism, 문아영's tactile painterly layers, 서나윤's athletic
confidence, 서지수's restrained luxury, 임세라's fashion-forward glamour, and
한서진's precise managerial polish.

Exact outfit and hair description strings are not duplicated across events or
characters. Repeated garment categories such as a slip dress are rewritten with
different cut, material, color, styling, exposure focus, and character intent.

## Files

Create one JSON profile for each of the following characters:

`노은화`, `도하영`, `문아영`, `박다정`, `박미현`, `박세연`, `서나윤`,
`서지수`, `오유림`, `유하린`, `이주은`, `이주희`, `이채영`, `이하은`,
`임세라`, `차소연`, `최유진`, `최윤서`, `한서진`.

Do not alter the existing 김민정 profile except where a test must read it as the
reference schema.

## Validation

Automated tests verify all 20 character profiles exist, names match filenames,
each character has the exact requested ten places in order, every event has the
required fields, each outfit pool has ten unique strings, each hair pool has five
unique strings, all descriptions are non-empty, and no event contains `arcs` or
legacy `place_rules`.

The tests also reject exact outfit or hair description duplication across the
entire profile collection. Finally, outline generation is exercised for every
character to prove the JSON-only generator can consume all profiles.
