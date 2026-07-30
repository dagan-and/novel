# AGENTS.md - wish-real 세션 가이드

## 프로젝트 개요

- wish-short(단편, 대사 금지, 매화 독립완결)와 reunion-reboot(장편 연재, 대사 허용, 라노벨체) 사이의 새 프로젝트다.
- 대사를 전면 허용하되 문장을 압축해서 쓰고, 화마다 리셋되지 않는 연속 서사를 쓴다.
- 세계관·인물은 wish-short/reunion-reboot/dual_life와 완전히 다른 새 설정이다. 회귀·타임루프 같은 하이 컨셉은 쓰지 않는다.

## 사용 원칙

- 에피소드 번호는 정렬용 ID가 아니라 실제 서사 진행 순서다. 이전 화 사건은 다음 화의 확정 과거로 자동 연결된다.
- 화당 분량은 3,000~5,000자를 기준으로 한다.
- 대사는 전면 허용한다. 단, 문장은 라노벨풍으로 짧게 압축한다 (`setting/문체규칙.md` 참고).
- 가변 정보(관계 단계, 최근 변화, 다음 압력, 성인씬 누적 횟수, 인게임 날짜, 현재 화수)는 `states/current_state.json` 한 곳에만 기록한다. `characters/` 파일에는 절대 중복 기록하지 않는다.
- `characters/` 파일은 고정 정보(외형·성격·배경·말투)만 담당한다.
- 성인 장면은 `setting/성인장면처리규칙.md`의 경량 페이드 방식을 따른다. wish-short 같은 무거운 컨텍스트 블록은 쓰지 않는다.
- 시나리오 작성 요청이 있기 전까지는 `episodes/` 원고를 생성하지 않는다.
- 세부 작업 순서는 `setting/워크플로우.md`를 따른다.

## wish-real 핵심 방향

(세계관·주인공·히로인 설정 확정 전. 아래 항목은 별도 브레인스토밍 세션에서 채운다.)

- 중심 감정:
- 시작 시점:
- 주인공 상태:
- 기본 생활권:
- 중심 관계:

## 파일 구조

```text
wish-real/
├── AGENTS.md
├── CLAUDE.md
├── 관계망.md
├── 연대기.md
├── states/
│   ├── current_state.json
│   └── recent_topics.json
├── planning/
│   ├── 시리즈개요.md
│   ├── 핵심컨셉.md
│   ├── 주제와정서.md
│   ├── 주인공설계.md
│   └── 캐릭터운영원칙.md
├── characters/
│   └── 캐릭터양식.md
├── setting/
│   ├── 워크플로우.md
│   ├── 문체규칙.md
│   └── 성인장면처리규칙.md
└── episodes/
    └── 001-100/
```

## 참조 우선순위

1. `AGENTS.md`
2. `setting/문체규칙.md`
3. `setting/워크플로우.md`
4. `states/current_state.json`
5. `연대기.md`
6. `planning/핵심컨셉.md`
7. `planning/주인공설계.md`
8. `planning/주제와정서.md`
9. `setting/성인장면처리규칙.md`
10. `characters/` (신규 히로인 등장 시에만)

## 신규 세션 시작 시 읽기 순서

1. `AGENTS.md` (현재 파일)
2. `states/current_state.json` — 현재 화수, 인게임 날짜, 관계 상태
3. `연대기.md` — 전체 타임라인

나머지는 요청 유형에 따라 추가로 읽는다. 화를 이어 쓸 때 `characters/` 파일은 신규 히로인이 처음 등장하는 경우가 아니면 열지 않아도 된다.

## 금지 사항

- wish-short, reunion-reboot, dual_life의 사건을 이 프로젝트의 확정 과거로 가져오지 않는다.
- 가변 정보를 `characters/` 파일에 중복 기록하지 않는다. `states/current_state.json`이 유일한 소스다.
- AI는 노골적인 성적 행위 묘사 본문을 직접 쓰지 않는다 (`setting/성인장면처리규칙.md` 참고).
- 상담, 회의, 감정 정리만으로 한 화를 끝내지 않는다.
- 새 인물을 단순 인원 보충용으로 투입하지 않는다.
- 초반부터 관계를 완성된 상태로 시작하지 않는다.
