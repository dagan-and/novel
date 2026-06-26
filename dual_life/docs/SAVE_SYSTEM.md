---
# SAVE_SYSTEM.md — 상태 저장 시스템

## 목적

장기 연재에서 설정이 충돌하지 않도록
모든 중요 상태를 기록하고 관리한다.

---

## 저장 파일 목록

| 파일 | 역할 |
|------|------|
| `states/current_state.json` | 현재 세계·날짜·관계 요약 |
| `states/investments.json` | 회귀 투자 내역 전용 |
| `states/회귀연대기.md` | 회귀 연도별 사건 기록 |
| `states/recent_topics.json` | 최근 20화 소재 목록 (패턴 방지) |

---

## current_state.json 형식

```json
{
  "last_updated": "날짜",
  "current_world": "현실 또는 회귀",

  "현실": {
    "date": "2025-12-07",
    "wife": { "name": "소영", "relationship": 90 },
    "son": { "age": 3, "relationship": 98 },
    "mother": { "relationship": 88 },
    "job": "앱 개발팀 차장",
    "assets_krw": 0
  },

  "회귀": {
    "date": "2005-01-01",
    "age": 15,
    "school": "고등학교 1학년",
    "happiness": 80,
    "health": 95,
    "relationships": []
  },

  "transferred_items": [],
  "episode_count": 0,
  "last_episode_summary": ""
}
```

---

## 업데이트 시점

다음 시점에 반드시 업데이트:
- 큰 투자 결정 후
- 인물 관계 변화 후
- 세계 이동 후
- 50화마다 전체 점검

---

## 인물 관계 기록

```json
{
  "name": "이름",
    "world": "회귀",
  "type": "친구 / 연인 / 사업 파트너",
  "intimacy": 0,
  "first_met": "날짜",
  "notes": ""
}
```
---
