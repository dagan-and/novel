# Novel — 프로젝트 안내

소설, 세계관, HTML 현황판과 개인 도구를 함께 보관하는 저장소입니다.
새 채팅에서 시작한다면 [새 세션 시작 안내](docs/START_HERE.md)를 먼저 읽고 원하는 프로젝트를 지정하세요.

## 지금 이어갈 작업

**《완전한 두 번째 삶》 (가제)**

- 원하는 경험: 직접 만든 세계관과 진행 상황을 HTML 화면으로 보며 계속 갱신하기.
- 게시 방향: GitHub Pages로 게시하고 스마트폰에서 같은 주소로 갱신 내용을 확인하기.
- 현재 단계: 공통 회귀일은 2005년 1월 1일입니다. 신체·인지의 수치와 측정 기준, 투자 편 첫 달 초안, 월별 관리 방식이 마련되었습니다.
- 다음 단계: [프로젝트 안내](second-life/README.md)에서 투자 편의 2005년 1월 첫 장면과 조사 항목을 확인하세요.

## 프로젝트 찾기

### 세계관·시뮬레이션

| 폴더 | 내용 | 먼저 볼 파일 |
| --- | --- | --- |
| [immortal-game](immortal-game/) | 불사자의 연대기, 상태·사건·기술 트리와 HTML 현황판 | [이어하기](immortal-game/RESUME.md), [현재 상태](immortal-game/game-state.json), [화면](immortal-game/chronicle.html) |
| [baekje-world-conquest](baekje-world-conquest/) | 백제 세계 정복 전황 브리핑과 턴별 HTML 연대기 | [README](baekje-world-conquest/README.md), [설정](baekje-world-conquest/setting.md), [화면](baekje-world-conquest/chronicle.html) |
| [honam](honam/) | 강림 백제 대체고대사, 기술·군사·세력·연대기 | [README](honam/README.md), [세계관](honam/세계관.md) |

### 소설·개요

| 폴더 | 내용 | 시작 위치 |
| --- | --- | --- |
| [second-life](second-life/) | 2005년으로 돌아온 김용식의 여러 삶. 투자 편부터 월별로 기록 | [작품·관리 안내](second-life/README.md), [투자 편](second-life/series/investing/README.md) |
| [dual_life](dual_life/) | 이중 현실 생활소설 | [README](dual_life/README.md), [세션 규칙](dual_life/AGENTS.md) |
| [reunion](reunion/) | 기존 reunion 시리즈 | [세션 규칙](reunion/AGENTS.md) |
| [reunion-reboot](reunion-reboot/) | 기존 reunion과 구분되는 별도 리부트 시리즈 | [세션 규칙](reunion-reboot/AGENTS.md) |
| [wish-real](wish-real/) | 원고·캐릭터·상태·HTML을 관리하는 시리즈 | [세션 규칙](wish-real/AGENTS.md) |
| [wish-short](wish-short/) | 단편 시리즈와 HTML 변환 도구 | [세션 규칙](wish-short/AGENTS.md) |
| [wish-outline](wish-outline/) | 개요·프로필·프롬프트 생성 도구와 자료 | [개요](wish-outline/episodes/), [문서](wish-outline/docs/), [실행 흐름](wish-outline/run_pipeline.py) |
| [stock-story-notes](stock-story-notes/) | 주식 소재 소설의 설정 메모와 참고 자료 | [통합 설정](stock-story-notes/kim-yongsik-misaki-integrated-setting-latest.md) |
| [novel-data](novel-data/) | 소설용 CSV, 통합 스프레드시트, 세계관 메모 | [메모](novel-data/notes/), [CSV](novel-data/csv/), [통합 자료](novel-data/master/) |

### 도구·개인 자료

| 폴더 | 내용 | 시작 위치 |
| --- | --- | --- |
| [VideoManager](VideoManager/) | Android 로컬 동영상 관리 앱 | [README](VideoManager/README.md) |
| [finance_fetcher](finance_fetcher/) | Yahoo Finance 시세 CSV 다운로드 도구 | [README](finance_fetcher/README.md) |
| [jeju-trip-2026-07-08](jeju-trip-2026-07-08/) | 제주 여행 일정과 HTML 자료 | [README](jeju-trip-2026-07-08/README.md) |
| [saju](saju/) | 사주 분석 문서와 HTML 자료 | [폴더 보기](saju/) |

### 기타 보존 항목

- `renuion-short/`: 현재 숨김 도구 상태 파일만 있는 폴더입니다. `reunion/`, `reunion-reboot/`와 구분하며, 이름 변경이나 삭제를 하지 않았습니다.
- `.bkit/`, `.superpowers/`: 기존 작업 도구의 상태·설정 폴더입니다. 작품 폴더로 취급하지 않습니다.

## HTML 보기와 게시

- [기존 웹 시작 페이지](index.html)는 현재 Dual Life 링크를 제공합니다. 전체 프로젝트 목록은 이 README를 기준으로 찾으세요.
- GitHub 파일 화면에서 HTML 소스를 여는 것과 GitHub Pages에서 실제 페이지를 보는 것은 다릅니다.
- Pages의 게시 브랜치·경로·배포 성공과 실제 HTTP 응답을 확인한 뒤 접속 주소를 안내합니다. 현재 배포 상태는 이 정리 작업에서 확인하지 않았습니다.
- 로컬 개발 서버는 임시 확인용입니다. 새 세션에서는 필요에 따라 다시 시작해야 합니다.

## 정리 범위

2026-11-18: 루트 README, 공통 세션 규칙, 새 세션 인계 문서를 추가했습니다. 기존 폴더 이름, 원고, 설정, 생성기와 HTML 경로는 유지했습니다. 프로젝트를 옮기거나 삭제하지 않았습니다.
