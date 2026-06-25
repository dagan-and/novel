# Wargame Playbook

## Purpose

This playbook is the copy-ready operator guide for the current conquest-campaign flow.

- Base flow stays on `간략 턴`
- `결전 턴` opens only for decisive clashes
- Choices must always be exactly `1 / 2 / 3`
- Results must stay `전과표 우선, 압살 포인트 포함`
- Keep the existing JSON schema unless a change is strictly required

## Current Rule Priority

- Treat this playbook and [RESUME.md](/Users/kys1207/novel-repo/immortal-game/RESUME.md) as the active rule set
- In this repository, a user message like `게임 시작해줘` should be treated as the resume shortcut defined in `RESUME.md`
- Older operation/tactical multi-input formats are deprecated for live play
- Never present `A/B/C` or combo inputs such as `1+5+8+11`

## When to Use Standard Turns

Use a standard turn when the player is choosing the next campaign push rather than resolving one decisive battle.

- Choose this for ordinary campaign pressure, posture shifts, and expansion choices
- Use it when one turn can be resolved through a single 3-choice decision
- Keep the focus on which enemy to break, where to expand, and how the immortal king applies overwhelming advantage

## When to Open Decisive Turns

Open a decisive turn only when a specific clash becomes important enough to deserve a battle-focused 3-choice prompt.

- Open it for a main-force collision on the primary axis
- Open it when a key crossing, port, fortress, or supply node decides the campaign
- Open it when the player is clearly trying to annihilate an enemy field army
- After a decisive clash, the flow normally returns to `간략 턴`

## Standard Turn Template

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AD XX년 X분기  |  캠페인 턴
상황: ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[이번 장의 목표]
- ...

[선택지]
1. ...
2. ...
3. ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
입력 예시: 2
```

Choice design:

- `1` should usually be the safer or steadier line
- `2` should usually be the aggressive expansion line
- `3` should usually be the immortal king / modern-knowledge / decisive-overmatch line

## Decisive Turn Template

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AD XX년 X분기  |  결전 턴
전투 목표: ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[전장]
- 좌익: ...
- 중앙: ...
- 우익: ...
- 후방: ...
- 퇴로: ...

[선택지]
1. ...
2. ...
3. ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
입력 예시: 3
```

## Result Template

```text
[전투 결과]
- 전선 변화: ...
- 아군 손실: ...
- 적 손실 추정: ...
- 보급 소모: ...
- 확보 지형: ...
- 압살 포인트: ...
- 장기 영향: ...

[전장 기록]
- 짧은 서사 3~5문장
```

The result block should always lead with battlefield effects, include one vivid `압살 포인트`, and only then add a short narrative tail.

## State Update Checklist

- Update `events.json` with the turn title, world context, and result line
- Update `game-state.json` for front-line status, losses, supply strain, and newly held positions
- Description-style state updates are acceptable when hard numbers do not fit cleanly
- Update `tech-tree.json` only if doctrine, logistics, or medical practice actually changed
- Do not regenerate `chronicle.html` unless explicitly requested
