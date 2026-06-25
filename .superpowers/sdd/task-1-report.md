DONE_WITH_CONCERNS

Changed files:
- /Users/kys1207/novel-repo/immortal-game/RESUME.md

Tests run:
- `rg -n "주행동|부행동|치트키" RESUME.md`
  - Result: `주행동` still matches in the new tactical-turn section required by the approved spec; the legacy `부행동` / `치트키` format is removed.
- `rg -n "부행동|치트키" RESUME.md`
  - Result: no matches
- `rg -n "주행동" RESUME.md`
  - Result: matches only in the tactical-turn input guidance (`주행동 1개`) and tactical example block
- `git diff -- RESUME.md`
  - Result: scope stayed within the resume turn-flow rewrite

Commits created:
- `a4d332de` `docs: switch resume guide to wargame turn flow`

Concerns:
- The brief's verification command still returns `주행동` because the approved spec explicitly uses `주행동` for `전술 턴`. This is a false positive against the old-format check, not a remaining legacy `주행동/부행동/치트키` resume structure.

---

Review-fix update:
- Updated the `RESUME.md` result example so the sample output now leads with the required order: front-line changes first, then losses, supply consumption, and captured ground, with equipment status after those priority items.
- Replaced the outdated fixed cadence line in the game defaults section with the approved mixed-wargame operation-rhythm guidance: `반년~1년`, `1분기`, and `1개월까지 축소 가능` depending on the situation.

Focused verification:
- `rg -n "^\\[전투 결과\\]|전선 변화:|아군 손실:|적 손실 추정:|보급 소모:|확보 지형:|포대 상태:" RESUME.md`
  - Confirmed the sample result block now leads with `전선 변화`, then losses, `보급 소모`, and `확보 지형`, with `포대 상태` following those priority items.
- `rg -n "턴 단위|반년~1년|1분기|1개월까지 축소 가능|평시 1년/턴|전시 1개월/턴" RESUME.md`
  - Confirmed the old fixed cadence wording is gone and the approved operation-rhythm guidance is present in the defaults section.

Additional concerns:
- None beyond the previously noted `주행동` false positive in the legacy-format grep check.

Recorded review-fix commit:
- `c470f4ed` `docs: fix task 1 resume review follow-up`
