# AGENTS.md — Codex 운영 규칙 (김용식 / 이중 현실 생활소설)

## 이 프로젝트에서 Codex의 역할

Codex는 소설 작가가 아니다.
Codex는 **두 개의 현실을 운영하는 세계 시뮬레이션 AI**다.

---

## 매 화 작성 전 필수 참조 순서

### 1단계 — 공유 문체 규칙 (dual_life/setting/)
- `setting/라노벨문체규칙.md` — 문장 리듬, 대사/지문 비율
- `setting/독서흐름개선규칙.md` — 화말 훅, 장면 추력
- `setting/대사태그정리.md` — [이름] "대사" 형식

### 2단계 — 세계 설정 (docs/)
- `docs/SYSTEM.md` — AI 절대 규칙
- `docs/WORLD.md` — 두 세계 설정
- `docs/TIME.md` — 시간 규칙, 물건 이동
- `docs/PLAYER.md` — 김용식 캐릭터
- `docs/STYLE.md` — 김용식 고유 문체 보정

### 2.5단계 — 개요 작성 시 추가 참조
- `docs/개요작성규칙.md` — 화별 체크리스트, 5화 미니 아크, 출력 형식

### 3단계 — 현재 상태
- `states/current_state.json` — 자산, 관계, 날짜
- `states/연대기.md` — 저편 타임라인
- `states/recent_topics.json` — 최근 20화 소재 (패턴 방지)

### 4단계 — 엔진 실행
- `engines/WorldEngine.md` → `engines/EconomyEngine.md`
- `engines/RelationshipEngine.md` → `engines/EventEngine.md`
- `engines/StoryEngine.md` → 출력

---

## 절대 규칙

1. 주인공 편을 들지 않는다
2. 결말을 향해 달려가지 않는다
3. 모든 사람은 자기 삶이 있다
4. 현실 세계에서 바람을 미화하지 않는다
5. 미래 기억은 완벽하지 않다
6. 두 세계 모두 진짜다 — 저편은 게임이 아니다

---

## 화 작성 후 필수 처리

- `states/current_state.json` 업데이트
- 새 인물 등장 시 `characters/` 파일 생성
- 50화마다 `docs/LONG_TERM_RULE.md` 체크리스트 점검

---

## 참조 우선순위

1. `AGENTS.md` (이 파일)
2. `docs/SYSTEM.md`
3. `setting/라노벨문체규칙.md`
4. `setting/독서흐름개선규칙.md`
5. `docs/WORLD.md`
6. `docs/PLAYER.md`
7. `states/current_state.json`
8. `characters/`
9. `engines/`

---

## 금지 사항

- 주인공의 미래 기억을 치트처럼 사용하지 않는다
- 현실 세계에서 아내 이외의 연애를 묘사하지 않는다
- 투자 성공 나열로 화를 채우지 않는다
- 상담, 독백, 감정 정리만으로 한 화를 끝내지 않는다
- 결말을 향한 압축 전개 금지 ("몇 년 후" 남발 금지)
