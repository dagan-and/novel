# wish-real 프로젝트 뼈대 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `wish-real` 프로젝트의 운영 뼈대(폴더 구조, AGENTS.md, states/*.json, planning/characters/setting 골격 문서)를 생성한다. 세계관·인물 실제 내용은 포함하지 않는다.

**Architecture:** wish-short/reunion-reboot의 AGENTS.md 패턴을 참고하되, 가변 정보(관계 단계·최근 변화·다음 압력·성인씬 횟수)를 `characters/`가 아닌 `states/current_state.json` 한 곳에만 기록하는 구조로 각색한다. 문서는 전부 마크다운/JSON 텍스트 파일이며 코드는 없다.

**Tech Stack:** Markdown, JSON. 검증은 `test -f`, `python3 -m json.tool`, `grep`로 수행한다 (코드가 없으므로 pytest 등 테스트 러너는 쓰지 않는다).

## Global Constraints

- 화당 분량: 3,000~5,000자 (스펙 "화 형식" 절)
- 대사 전면 허용, 문장은 압축해서 짧게 (스펙 "화 형식" 절)
- 에피소드 번호 = 실제 서사 순서, 정렬용 ID 아님 (스펙 "화 형식" 절)
- 가변 정보(관계 단계·최근 변화·다음 압력·성인씬 누적 횟수·인게임 날짜·현재 화수)는 `states/current_state.json`에만 기록, `characters/` 파일에 중복 기록 금지 (스펙 "정보 소유권 규칙" 절)
- 성인 장면: 무거운 컨텍스트 블록 없이 경량 페이드 처리, AI는 노골적 본문을 직접 쓰지 않음 (스펙 "성인 장면 처리 규칙" 절)
- 세계관/주인공/히로인 실제 내용은 이 계획의 범위 밖 (스펙 "비목표" 절)

---

## Task 1: 루트 스켈레톤 + CLAUDE.md

**Files:**
- Create: `wish-real/CLAUDE.md`
- Create: `wish-real/.gitkeep` (임시, Task 10에서 실제 파일들이 채워지면 제거되어도 무방)

**Interfaces:**
- Consumes: 없음 (최초 태스크)
- Produces: `wish-real/` 디렉터리 자체. 이후 모든 태스크가 이 디렉터리 하위에 파일을 생성한다.

- [ ] **Step 1: 디렉터리 존재 확인**

Run: `test -d /Users/kys1207/novel-repo/wish-real && echo EXISTS || echo MISSING`
Expected: `EXISTS` (이미 Write 도구로 spec/plan 문서를 써서 디렉터리가 생성되어 있음)

- [ ] **Step 2: CLAUDE.md 작성**

파일 내용 (`wish-real/CLAUDE.md`):

```
@AGENTS.md
```

- [ ] **Step 3: 파일 생성 확인**

Run: `cat /Users/kys1207/novel-repo/wish-real/CLAUDE.md`
Expected: `@AGENTS.md` 한 줄 출력

- [ ] **Step 4: Commit**

```bash
cd /Users/kys1207/novel-repo
git add wish-real/CLAUDE.md
git commit -m "Add wish-real CLAUDE.md pointer"
```

---

## Task 2: AGENTS.md (핵심 운영 가이드)

**Files:**
- Create: `wish-real/AGENTS.md`

**Interfaces:**
- Consumes: Task 1의 `wish-real/` 디렉터리
- Produces: 이후 모든 setting/planning 문서가 참조하는 파일 구조 다이어그램과 참조 우선순위. Task 3~9는 이 파일이 나열하는 경로와 정확히 일치해야 한다.

- [ ] **Step 1: AGENTS.md 작성**

파일 내용 (`wish-real/AGENTS.md`):

```markdown
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
```

- [ ] **Step 2: 필수 섹션 존재 확인**

Run: `grep -c '^## ' /Users/kys1207/novel-repo/wish-real/AGENTS.md`
Expected: `7` (프로젝트 개요, 사용 원칙, 핵심 방향, 파일 구조, 참조 우선순위, 신규 세션 시작 시 읽기 순서, 금지 사항)

- [ ] **Step 3: Commit**

```bash
cd /Users/kys1207/novel-repo
git add wish-real/AGENTS.md
git commit -m "Add wish-real AGENTS.md operating guide"
```

---

## Task 3: states/current_state.json + states/recent_topics.json

**Files:**
- Create: `wish-real/states/current_state.json`
- Create: `wish-real/states/recent_topics.json`

**Interfaces:**
- Consumes: 없음 (Task 2의 AGENTS.md가 이 경로들을 참조하지만 파일 내용에 의존하지 않음)
- Produces: `current_state.json`의 키 이름(`current_episode`, `in_story_date`, `protagonist.name`, `protagonist.status`, `heroines`, `last_updated_episode`)과 `recent_topics.json`의 키 이름(`recent_topics`)은 Task 7(워크플로우.md)과 Task 9(성인장면처리규칙.md)가 그대로 인용한다. 이후 실제 화 작성 시에도 이 키 이름을 그대로 갱신한다.

- [ ] **Step 1: current_state.json 작성**

파일 내용 (`wish-real/states/current_state.json`):

```json
{
  "current_episode": 0,
  "in_story_date": "",
  "protagonist": {
    "name": "",
    "status": ""
  },
  "heroines": {},
  "last_updated_episode": 0
}
```

- [ ] **Step 2: recent_topics.json 작성**

파일 내용 (`wish-real/states/recent_topics.json`):

```json
{
  "recent_topics": []
}
```

- [ ] **Step 3: JSON 유효성 검증**

Run: `python3 -m json.tool /Users/kys1207/novel-repo/wish-real/states/current_state.json > /dev/null && python3 -m json.tool /Users/kys1207/novel-repo/wish-real/states/recent_topics.json > /dev/null && echo VALID`
Expected: `VALID` (에러 없이 출력)

- [ ] **Step 4: Commit**

```bash
cd /Users/kys1207/novel-repo
git add wish-real/states/current_state.json wish-real/states/recent_topics.json
git commit -m "Add wish-real state tracking JSON files"
```

---

## Task 4: 관계망.md + 연대기.md

**Files:**
- Create: `wish-real/관계망.md`
- Create: `wish-real/연대기.md`

**Interfaces:**
- Consumes: 없음
- Produces: `연대기.md`의 표 헤더(`| 화 | 인게임 날짜 | 핵심 사건 |`)는 Task 7(워크플로우.md)의 "화 작성 완료 후" 절차가 그대로 채워 넣는 대상이다.

- [ ] **Step 1: 관계망.md 작성**

파일 내용 (`wish-real/관계망.md`):

```markdown
# 관계망

(세계관 확정 전. 히로인이 정해지면 인물별 관계도를 여기에 정리한다.)
```

- [ ] **Step 2: 연대기.md 작성**

파일 내용 (`wish-real/연대기.md`):

```markdown
# 연대기

(세계관 확정 전. 화별 사건 타임라인을 여기에 순서대로 기록한다.)

| 화 | 인게임 날짜 | 핵심 사건 |
|---|---|---|
```

- [ ] **Step 3: 파일 존재 확인**

Run: `test -f /Users/kys1207/novel-repo/wish-real/관계망.md && test -f /Users/kys1207/novel-repo/wish-real/연대기.md && echo BOTH_EXIST`
Expected: `BOTH_EXIST`

- [ ] **Step 4: Commit**

```bash
cd /Users/kys1207/novel-repo
git add wish-real/관계망.md wish-real/연대기.md
git commit -m "Add wish-real relationship map and timeline skeletons"
```

---

## Task 5: planning/ 5개 문서

**Files:**
- Create: `wish-real/planning/시리즈개요.md`
- Create: `wish-real/planning/핵심컨셉.md`
- Create: `wish-real/planning/주제와정서.md`
- Create: `wish-real/planning/주인공설계.md`
- Create: `wish-real/planning/캐릭터운영원칙.md`

**Interfaces:**
- Consumes: 없음
- Produces: 다섯 파일 모두 세계관 확정 후 채워질 빈 골격. 이후 태스크는 이 파일들을 참조하지 않는다.

- [ ] **Step 1: 시리즈개요.md 작성**

```markdown
# 시리즈 개요

(세계관 확정 후 작성. 시리즈 전체 컨셉, 톤, 목표 분량 등을 정리한다.)
```

- [ ] **Step 2: 핵심컨셉.md 작성**

```markdown
# 핵심 컨셉

(세계관 확정 후 작성. 이야기를 굴리는 핵심 엔진, 반복 가능한 갈등 구조를 정리한다.)
```

- [ ] **Step 3: 주제와정서.md 작성**

```markdown
# 주제와 정서

(세계관 확정 후 작성. 지향하는 정서 키워드와 피해야 할 정서를 정리한다.)
```

- [ ] **Step 4: 주인공설계.md 작성**

```markdown
# 주인공 설계

(세계관 확정 후 작성. 주인공의 장점·약점·장면 운용 방식을 정리한다.)
```

- [ ] **Step 5: 캐릭터운영원칙.md 작성**

```markdown
# 캐릭터 운영 원칙

(세계관 확정 후 작성. 히로인 투입·퇴장 원칙, 다인 씬 규칙 등을 정리한다.)
```

- [ ] **Step 6: 5개 파일 존재 확인**

Run: `ls /Users/kys1207/novel-repo/wish-real/planning/ | wc -l`
Expected: `5`

- [ ] **Step 7: Commit**

```bash
cd /Users/kys1207/novel-repo
git add wish-real/planning/
git commit -m "Add wish-real planning document skeletons"
```

---

## Task 6: characters/캐릭터양식.md

**Files:**
- Create: `wish-real/characters/캐릭터양식.md`

**Interfaces:**
- Consumes: Task 2의 AGENTS.md "정보 소유권" 원칙 (고정 정보만 담당)
- Produces: 향후 실제 히로인 파일(`characters/[이름].md`)이 복사해서 쓸 양식. 필드 이름(`외형`, `성격`, `배경`)은 향후 히로인 파일 작성 시 그대로 재사용된다.

- [ ] **Step 1: 캐릭터양식.md 작성**

파일 내용 (`wish-real/characters/캐릭터양식.md`):

```markdown
# 캐릭터 양식

이 파일은 양식 참고용이며 히로인이 아니다. 새 히로인 추가 시 이 양식을 복사해서 `characters/[이름].md`로 저장한다.

이 프로젝트에서 캐릭터 파일은 **고정 정보만** 담당한다. 관계 단계·최근 변화·다음 압력·성인씬 누적 횟수 같은 가변 정보는 `states/current_state.json`에만 기록하고 이 파일에는 적지 않는다.

## 기본 정보

- 이름:
- 나이:
- 주인공과의 접점: (생활권 등)

### 외형

- 체형:
- 얼굴:
- 헤어:
- 분위기:

### 성격

- 성격 키워드:
- 감정 표현 방식:
- 주인공 앞에서의 반응 패턴:

### 배경

- 소속/생활권:
- 남자친구 유무:
```

- [ ] **Step 2: 필수 섹션 존재 확인**

Run: `grep -c '^### ' /Users/kys1207/novel-repo/wish-real/characters/캐릭터양식.md`
Expected: `3` (외형, 성격, 배경)

- [ ] **Step 3: Commit**

```bash
cd /Users/kys1207/novel-repo
git add wish-real/characters/캐릭터양식.md
git commit -m "Add wish-real character template"
```

---

## Task 7: setting/워크플로우.md

**Files:**
- Create: `wish-real/setting/워크플로우.md`

**Interfaces:**
- Consumes: Task 3의 `states/current_state.json`/`states/recent_topics.json` 키 이름, Task 4의 `연대기.md` 표 형식
- Produces: 화 작성 전/후 절차. Task 8(문체규칙.md), Task 9(성인장면처리규칙.md)를 참조 대상으로 인용한다.

- [ ] **Step 1: 워크플로우.md 작성**

파일 내용 (`wish-real/setting/워크플로우.md`):

```markdown
# 워크플로우

## 신규 세션 시작

1. `AGENTS.md`를 읽는다.
2. `states/current_state.json`을 읽고 현재 화수, 인게임 날짜, 히로인별 관계 상태를 파악한다.
3. `연대기.md`를 읽고 전체 타임라인을 파악한다.

## 화 작성

1. `setting/문체규칙.md`를 참고해 대사 허용 + 압축 문체 기준을 확인한다.
2. 이번 화에 처음 등장하는 히로인이 있다면 해당 `characters/[이름].md`를 읽어 고정 정보를 확인한다.
3. `states/recent_topics.json`을 확인해 최근 화와 소재가 겹치지 않게 한다.
4. 화당 3,000~5,000자 분량으로 작성한다. 에피소드 번호는 실제 서사 순서이므로 이전 화 사건을 확정 과거로 이어받는다.
5. 성인 장면이 필요하면 `setting/성인장면처리규칙.md`의 경량 페이드 방식을 따른다.

## 화 작성 완료 후

1. `states/current_state.json`을 갱신한다: `current_episode`, `in_story_date`, 관련 히로인의 `stage`/`recent_change`/`next_pressure`/`adult_scene_count`, `last_updated_episode`.
2. `states/recent_topics.json`에 이번 화 소재를 추가하고, 20개를 넘으면 가장 오래된 항목부터 정리한다.
3. `연대기.md` 표에 이번 화 행을 추가한다.
```

- [ ] **Step 2: 필수 섹션 존재 확인**

Run: `grep -c '^## ' /Users/kys1207/novel-repo/wish-real/setting/워크플로우.md`
Expected: `3` (신규 세션 시작, 화 작성, 화 작성 완료 후)

- [ ] **Step 3: Commit**

```bash
cd /Users/kys1207/novel-repo
git add wish-real/setting/워크플로우.md
git commit -m "Add wish-real workflow doc"
```

---

## Task 8: setting/문체규칙.md

**Files:**
- Create: `wish-real/setting/문체규칙.md`

**Interfaces:**
- Consumes: 없음
- Produces: 대사 태그 규칙("2인 장면 화자 태그 금지, 3인 이상만 사용")은 기존 wish-short 세션 피드백 메모리와 동일한 결로 유지된다.

- [ ] **Step 1: 문체규칙.md 작성**

파일 내용 (`wish-real/setting/문체규칙.md`):

```markdown
# 문체 규칙

## 대사

- 대사를 전면 허용한다. `[이름] "대사"` 형식이든 인용부호만 쓰는 형식이든 자유롭게 쓰되, 한 작품 안에서는 형식을 통일한다.
- 2인 장면에서는 화자 태그(`[이름]`)를 쓰지 않는다. 대사 앞뒤 맥락으로 화자가 구분되게 쓴다.
- 3인 이상이 동시에 등장하는 장면에서만 화자 태그를 써서 혼동을 막는다.

## 문장

- 문장은 짧게 끊는다. 한 문장에 정보 하나만 담는다.
- 감정 해설(`~라고 생각했다`, `~를 느꼈다`)보다 행동·감각·표정으로 감정을 드러낸다.
- 묘사가 길어질 것 같으면 대사나 행동으로 끊는다. 라노벨처럼 리듬감 있게 진행 속도를 유지한다.
- 같은 문장 구조가 3문장 이상 반복되면 길이나 구조를 바꾼다.

## 분량

- 화당 3,000~5,000자를 기준으로 한다. 크게 벗어나면 장면을 나누거나 압축한다.
```

- [ ] **Step 2: 필수 섹션 존재 확인**

Run: `grep -c '^## ' /Users/kys1207/novel-repo/wish-real/setting/문체규칙.md`
Expected: `3` (대사, 문장, 분량)

- [ ] **Step 3: Commit**

```bash
cd /Users/kys1207/novel-repo
git add wish-real/setting/문체규칙.md
git commit -m "Add wish-real style rules"
```

---

## Task 9: setting/성인장면처리규칙.md

**Files:**
- Create: `wish-real/setting/성인장면처리규칙.md`

**Interfaces:**
- Consumes: Task 3의 `states/current_state.json`의 `heroines.<이름>.adult_scene_count` 키
- Produces: 없음 (최종 소비자)

- [ ] **Step 1: 성인장면처리규칙.md 작성**

파일 내용 (`wish-real/setting/성인장면처리규칙.md`):

```markdown
# 성인 장면 처리 규칙

## 기본 원칙

- AI는 노골적인 성적 행위 묘사 본문을 직접 쓰지 않는다. 이는 스타일 선택이 아니라 지켜야 하는 경계다.
- wish-short처럼 장소·의상·표정·손과 시선 포인트 등을 나열하는 무거운 컨텍스트 블록은 쓰지 않는다.
- 로맨틱한 긴장감, 스킨십 직전까지의 흐름은 대사를 포함해 자연스럽게 서술한다.

## 페이드 처리

- 장면이 노골적인 지점에 도달하면 한두 줄짜리 상황 메모로 페이드 처리하고 장면을 마무리한다.
- 페이드 메모는 분위기·다음 장면 전환 정도만 담고, 신체 부위나 행위를 직접 묘사하지 않는다.

### 예시

> 문이 닫히고 방 안의 조명이 꺼졌다. 다음 장면은 다음 날 아침, 나른한 얼굴로 이어진다.

> 두 사람 사이의 거리가 사라졌다. 그 뒤의 시간은 지나가고, 창밖이 밝아올 무렵 이야기가 다시 시작된다.

## 운영 규칙

- 페이드 지점 이후 문장에서 "그날 밤", "일이 있고 나서" 같은 메타 설명 대신, 다음 장면의 구체적 시간·장소·인물 상태로 바로 이어간다.
- `states/current_state.json`의 해당 히로인 `adult_scene_count`를 1 증가시킨다.
```

- [ ] **Step 2: 필수 섹션 존재 확인**

Run: `grep -c '^## ' /Users/kys1207/novel-repo/wish-real/setting/성인장면처리규칙.md`
Expected: `3` (기본 원칙, 페이드 처리, 운영 규칙)

- [ ] **Step 3: Commit**

```bash
cd /Users/kys1207/novel-repo
git add wish-real/setting/성인장면처리규칙.md
git commit -m "Add wish-real adult scene fade-handling rules"
```

---

## Task 10: episodes/001-100 폴더 + 전체 구조 검증

**Files:**
- Create: `wish-real/episodes/001-100/.gitkeep`

**Interfaces:**
- Consumes: Task 1~9에서 생성된 모든 파일
- Produces: 없음 (최종 검증 태스크)

- [ ] **Step 1: episodes 폴더 생성**

파일 내용 (`wish-real/episodes/001-100/.gitkeep`):

```
```

(빈 파일. git은 빈 디렉터리를 추적하지 않으므로 자리 표시용 파일을 둔다.)

- [ ] **Step 2: 전체 구조가 AGENTS.md의 파일 구조 절과 일치하는지 확인**

Run:
```bash
cd /Users/kys1207/novel-repo/wish-real
test -f CLAUDE.md && \
test -f AGENTS.md && \
test -f 관계망.md && \
test -f 연대기.md && \
test -f states/current_state.json && \
test -f states/recent_topics.json && \
test -f planning/시리즈개요.md && \
test -f planning/핵심컨셉.md && \
test -f planning/주제와정서.md && \
test -f planning/주인공설계.md && \
test -f planning/캐릭터운영원칙.md && \
test -f characters/캐릭터양식.md && \
test -f setting/워크플로우.md && \
test -f setting/문체규칙.md && \
test -f setting/성인장면처리규칙.md && \
test -d episodes/001-100 && \
echo ALL_PRESENT
```
Expected: `ALL_PRESENT`

- [ ] **Step 3: Commit**

```bash
cd /Users/kys1207/novel-repo
git add wish-real/episodes/001-100/.gitkeep
git commit -m "Add wish-real episodes folder"
```

---

## Post-plan note (범위 밖)

세계관, 주인공 프로필, 히로인 구성은 이 계획에 포함하지 않는다. `planning/`, `characters/[이름].md`의 실제 내용은 별도 브레인스토밍 세션에서 세계관이 정해진 뒤 채운다.
