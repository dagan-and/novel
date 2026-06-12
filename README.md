# 왕의 귀환 — 소설 관리 저장소

Claude Code와 협업하여 집필하는 웹소설 프로젝트입니다.  
마크다운으로 원고를 작성하고, 스크립트로 HTML로 변환합니다.

---

## 디렉토리 구조

```
.
├── episodes/       # 본편 원고 (1화.md ~ n화.md)
├── html/           # 변환된 HTML 출력 (convert.js 실행 후 생성)
├── characters/     # 인물 프로필
│   ├── 주인공/
│   ├── 내전/
│   ├── 신하/
│   └── 외부/
├── setting/        # 세계관 설정
│   ├── master.md       # 집필 규칙 전체
│   ├── HISTORY.md      # 화수·마일스톤
│   ├── RELATIONS.md    # 인물 관계·충성도·복선
│   ├── TERRITORY.md    # 영토·자원·건축물
│   └── TECH.md         # 도입 기술 기록
├── idea/           # 아이디어 메모
├── prompt/         # 이미지 생성 프롬프트
├── images/         # 캐릭터 이미지
└── CLAUDE.md       # Claude Code 세션 가이드
```

---

## 변환 스크립트

```bash
# 에피소드 MD → HTML 변환
node convert.js

# 인물 프로필 변환
node convert-profile.js

# 세계관 설정 변환
node convert-setting.js
```

---

## Claude Code와 집필하기

`CLAUDE.md`에 세션 시작 시 참조할 파일 순서와 워크플로우가 정의되어 있습니다.  
새 세션을 시작하면 Claude Code가 자동으로 설정을 읽고 이전 서사를 이어받습니다.
