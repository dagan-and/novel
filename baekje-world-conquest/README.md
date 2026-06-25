# Baekje World Conquest

한글 전황 브리핑 형식으로 이어지는 관전형 전쟁 시뮬 프로젝트다. 통일 백제가 현대 지식을 가진 불사의 초월자 `천인`의 지휘 아래 국가 체질을 바꾸고, 그 격차로 세계 정복을 향해 나아간다.

## Structure

- `setting.md`: 기본 세계관과 전제
- `factions.md`: 주요 세력 개요
- `rules.md`: 시뮬 규칙과 턴 진행 원칙
- `turns/`: 상세 마크다운 턴 기록
- `turns.json`: HTML 생성을 위한 짧은 턴 데이터
- `generate.py`: 전황 브리핑 HTML 생성기
- `chronicle.html`: 턴별 넘김이 가능한 한글 연대기 화면

## Usage

`python3 generate.py`를 실행하면 `turns.json`을 읽어서 `chronicle.html`을 다시 만든다.
