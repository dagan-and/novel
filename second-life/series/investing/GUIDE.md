# 투자 편 작업 가이드

새 세션은 이 문서 하나만 읽고 시작한다. 여기에는 무엇을 어떤 순서로 읽고, 어디에 무엇을 쓰고, 한 달을 어떻게 진행·마감·게시하는지가 모두 들어 있다. 지금 어디까지 왔는지는 [RESUME.md](RESUME.md) 한 장에 있다.

---

## 0. 시작할 때 (5분)

1. 이 문서를 읽는다.
2. [RESUME.md](RESUME.md)에서 현재 위치·미결 질문·다음 행동을 확인한다.
3. `state.json`을 본다.
   - `last_confirmed_month`: 마감된 마지막 달
   - `working_month`: 초안을 쓰고 있는 달(없으면 null)
   - `next_month`: 다음에 제안서를 낼 달
4. 검사를 돌린다. `python3 scripts/check_continuity.py`(second-life 폴더에서). 실패하면 그것부터 고친다.
5. 작업할 달의 본문 `months/YYYY-MM.md`와, 있으면 제안서 `planning/YYYY-MM-proposal.md`를 읽는다.

공통 설정(`../../base/`)은 필요한 문서만 연다. 생일·능력·기억은 base가 기준이다. 다른 작품이나 다른 편의 설정은 가져오지 않는다.

---

## 1. 이 작품의 형식 (어기면 안 되는 것)

- **용식의 1인칭 월간 경험 기록.** 무엇을 경험·파악·선택·구축했는지 설명한다. 인물 대화, 따옴표 독백, 전지적 소설 장면은 쓰지 않는다.
- 작가가 설정을 밝히는 말투("~로 잡았다", "기준안이다")를 본문에 쓰지 않는다. 그런 설명은 본문 머리 인용문(`>`)이나 planning에 둔다.
- 새 사건·금액·인물·전개는 **먼저 사용자와 고른다(D025).** 아이디어나 검토 요청을 본문 작성·마감·게시 지시로 넓히지 않는다. 사용자가 이미 정한 것은 다시 묻지 않는다.
- 미래 월의 성적·관계·금액이 과거 월 화면에 보이면 안 된다.
- 모르는 값은 `null`(미정)로 둔다. 0으로 채우지 않는다.

---

## 2. 파일 지도

| 파일 | 내용 | 누가 쓰나 | 공개 |
| --- | --- | --- | --- |
| `GUIDE.md` (이 문서) | 작업 방법 | 방법이 바뀔 때만 | X |
| `RESUME.md` | 현재 위치 한 장. **매번 통째로 다시 쓴다** | 사람 | X |
| `state.json` | 마감 월·작업 월·다음 제안 월 | 사람(마감 때) | X |
| `months/YYYY-MM.md` | 월간 본문. `## 소제목` 단위로 현황판에 표시 | 사람 | O(HTML로) |
| `planning/YYYY-MM-proposal.md` | 다음 달 제안서 (아래 4장) | 사람 | X |
| `planning/YYYY-MM.md` | 그달 합의 내용·작성 기준 | 사람 | X |
| `research/monthly/YYYY-MM-context.md` | 그달 실제 시대 사실 조사(출처·확인수준) | 사람 | X |
| `research/*` | 그 밖의 시대·학교·게임·비용 조사 | 사람 | X |
| `data/records.json` | 결정 D·사건 E·할 일 T·미정 U·변경 C·월 목록·이어지는 활동 O | 사람 | X |
| `data/ledger.json` | **개인 현금의 유일한 원장.** 규칙(rules)과 지출(spending) | 사람 | X |
| `data/metrics.json` | 월별 사이트 수치·시험·체격·APM·관계·예산. 일부는 자동 계산 | 사람+스크립트 | O(현황판에 포함) |
| `snapshots/YYYY-MM.json` | 마감한 달의 월말 상태 | 마감 때 생성 | X |
| `characters/person-NNN.md` | 인물 프로필 원본 → HTML 생성 | 사람 | O(HTML로) |
| `history/` | 대체된 옛 장부·인계 문서 보존 | 손대지 않음 | X |
| `dashboard.html`, `characters/*.html`, `index.html` | **생성물. 직접 고치지 않는다** | 스크립트 | O |

### metrics.json에서 사람이 쓰는 칸과 자동 칸

- 사람이 쓴다: `monthly[].visitor_days / pageviews / ad_pageviews / publisher_rpm_usd / investment_*`, `academics`·`additional_exams`(시험), `body`, `starcraft`, `standing`, `relationships`, `cost_model`, `personal_spending_budget`, `personal_assets`.
- 스크립트가 덮어쓴다(손대지 말 것): `daily`, `monthly[].ad_revenue_usd`(RPM이 있으면), `cumulative_*`, `average_*`, `cash_received_usd`, `personal_cash_krw`, `finances`, `status`(마감 월), `revenue_sharing`, 시험 `simple_average`.

---

## 3. 상태값 사전

| 대상 | 값 | 뜻 |
| --- | --- | --- |
| 결정·사건 | `confirmed` | 사용자가 정했거나 마감으로 확정 |
| | `draft` | 작가 초안. 읽을 수는 있으나 마감 전 |
| | `superseded` | 대체됨. `superseded_by`에 대체한 ID를 적는다. 일부만 바뀐 경우 `partially_superseded_by` |
| 월(records.months) | `confirmed` / `draft` | 마감 여부 |
| metrics 월 | `closed` / `story_estimate` / `pending` | 마감 / 수치는 있으나 미마감 / 수치 미정 |
| 현금 범위 | `closed` / `provisional` / `unknown` | 마감 잔액 / 미마감(생활비 일부 미기록) / 계산 불가 |
| 값 | `null` | 미정. 0과 다르다 |

사건 ID 규칙: 결정 `D###`, 사건 `E###`, 할 일 `T###`, 미정 `U###`, 변경 이력 `C###`, 지출 `S###`, 이어지는 활동 `O###`. 마지막 번호 다음을 쓴다.

---

## 4. 한 달 진행 순서

### 1단계. 다음 달 제안서 (본문을 쓰기 전에 항상)

1. **이어지는 활동 점검:** `records.ongoing_threads`(O001~)와 지난달 미완료 일을 확인한다. 각 활동이 계속·변경·종료인지 적는다. 근거 없이 빠뜨리지 않는다.
2. **시대 조사:** `research/monthly/YYYY-MM-context.md`를 만든다. 다음을 출처 URL과 날짜, 확인수준(확인/경향/추정/미확인)과 함께 표로 정리한다. 미확인은 미확인이라고 쓴다.
   - 학교 일정(시험·방학·행사, 당시 고교 학년의 특징)
   - 날씨·계절
   - 사이트 관련 게임(WoW·디아2 패치와 이벤트, 한국 서버 적용일)
   - 스타 리그 등 10대 관심사
   - 영화·드라마·음악·싸이월드·기기 등 문화
   - 코스피·코스닥·금리·환율(투자 편의 배경)
   - 사회 뉴스
   - 그 나이(15~16세 고교생)가 그달 할 법한 일 후보와 근거
3. **제안서 작성:** `planning/YYYY-MM-proposal.md`. 아래 서식을 따른다.
4. **사용자에게 짧게 제시**하고 고르게 한다. 답이 오기 전에는 본문·지표·원장을 건드리지 않는다.

제안서 서식:

```
# YYYY년 M월 제안서
> 상태: 제안(미채택). 근거 조사: research/monthly/YYYY-MM-context.md
## 1. 지난달에서 이어받는 것   (활동별 표: 지난달 끝 상태 → 이달 할 일)
## 2. 그달 실제 달력          (확인된 사실과 이야기에 쓰는 방식, 미확인 목록)
## 3. 돈 흐름 예고            (이달 말 수령액 = 지난달 발생분, 환율, 정해야 할 수치)
## 4. 큰 흐름 후보 A/B/C      (각 3~5줄, 권장 표시)
## 5. 정해 주실 것            (번호 붙인 단답형 질문, 예시값 포함)
## 6. 넣지 않는 것
```

### 2단계. 합의 기록

- 사용자가 고른 내용은 `records.decisions`에 `D###`로 적는다. 필드는 `status`, `domain`(story·site·school·body·relation·money·life·publish·workflow), `summary`, `source`(사용자 말 요약과 날짜)다.
- 이전 결정을 바꾸면 이전 항목에 `superseded_by`(일부만이면 `partially_superseded_by`)를 달고, `records.changes`에 `C###`(대상·이유·이전 값)를 남긴다.
- 그달 작성 기준은 `planning/YYYY-MM.md`에 짧게 적는다.

### 3단계. 본문 쓰기 (`months/YYYY-MM.md`)

- 첫 줄 `# YYYY년 M월 · 제목`, 다음 줄 `> 머리말`(무엇이 사용자 설정이고 무엇이 모형인지 한 줄).
- `## 소제목` 4~6개. 흐름: 배경과 조건 → 발견한 변화 → 선택과 근거 → 실행하며 확인한 것 → 월말에 달라진 점과 다음 문제.
- 사이트·학교·관계·몸·돈을 이어서 다룬다. 능력은 찬사보다 이해·판단·실행에서 보이는 차이로 쓴다. 미래 기억, 강화된 뇌, 새로 조사한 정보는 구분한다.
- **숫자 규칙:**
  - 정밀한 수치는 데이터에 한 번만 둔다. 본문에는 이야기에 필요한 수치만 쓴다.
  - 렌더러가 `숫자+달러`를 1달러=1000원으로 자동 환산한다. 실제 수령액(월평균 환율)은 본문에 **원화로만** 쓴다. 예: "그달 평균 환율 1,001.84원으로 192,353원".
  - 본문의 원화 금액은 `refresh` 결과(`metrics.monthly[].finances`)와 반드시 같게 쓴다.

### 4단계. 데이터 입력

| 바뀐 것 | 쓰는 곳 |
| --- | --- |
| 사이트 유입·광고 | `metrics.monthly`의 그달 행: `section_pageviews`(섹션별 PV, 합이 pageviews), `pageviews`, `ad_pageviews`, `visitor_days`(PV×0.209), `publisher_rpm_usd`, `basis`(근거 한 줄). 아래 5-1장 모델로 정한다. 미정이면 null |
| 새 달 추가 | `metrics.monthly` 행, `cost_model.monthly` 행, `records.months` 항목을 함께 추가 |
| 지출 | `ledger.spending`에 **한 달에 한 줄**(D049): `S###`, month, amount_krw(대략적인 총액, 예: 200000), memo(예: "데이트·교통·사이트"), 있으면 event_ids. 항목별로 나누지 않는다. 본문에도 "이번 달 20만원 정도" 수준으로 쓴다 |
| 다음 달 생활비 계획 | `metrics.personal_spending_budget.monthly` (계획일 뿐 현금에 반영되지 않음) |
| 시험 | 새 시험은 `metrics.additional_exams`에 객체 하나(school, exam, story_month, subjects, rank_in_grade, research, question_point_values 2·3·4). 점수는 2·3·4점 문항으로 만들 수 있는 값이어야 한다 |
| 체격 | `metrics.body`에 날짜별 점 추가. 제지방 = 체중×(1−체지방률). 골격근량은 null |
| 스타 | `metrics.starcraft` 월별 행(D035로 7월 이후 직접 플레이 기록은 제외) |
| 학교·학원 평판 | `metrics.standing` (정성 기록, 인기 점수 금지) |
| 인물 | `metrics.relationships`(phases, profile_href, portrait) + `characters/person-NNN.md` |
| 투자 | `metrics.monthly[].investment_assets_krw / investment_realized_pnl_krw / holdings / trade_count`, `metrics.investments`. 매수 대금은 `ledger.spending`(category `investment`)으로 현금에서 뺀다 |
| 사건 | `records.events`에 `E###`: status, story_date, summary, source, decision_ids |

### 5단계. 생성과 검사 (second-life 폴더에서)

```
python3 scripts/refresh_metrics.py   # 일별 배분·누적·현금·분배 계산
python3 scripts/check_continuity.py  # 구조·수치·원장·마감 검사
python3 scripts/render_investing.py  # dashboard.html·프로필·옛 주소 생성
```

검사가 실패하면 원본을 고친다. 생성 HTML이나 자동 칸을 손으로 맞추지 않는다. 화면 확인은 `dashboard.html?month=YYYY-MM`을 브라우저로 열어서 한다.

### 6단계. 월 마감 (사용자가 "마감" 또는 "확정"이라고 할 때만)

1. 그달 지출을 `ledger.spending`에 빠짐없이 넣는다(계획표를 실제로 쓰기로 했으면 옮겨 적는다).
2. `ledger.closed_through`, `records.last_confirmed_month`, `state.last_confirmed_month`를 그달로 바꾼다.
3. `records.months[그달].status = confirmed`로 바꾸고, 그달까지의 `draft` 사건은 `confirmed`(또는 대체된 것은 `superseded`)로 정리한다.
4. `state.month_end_state`를 새 스냅샷으로 바꾸고, `snapshots/YYYY-MM.json`을 만든다(현금·흐름·수령·미수령·사건 ID).
5. 5단계 명령을 다시 돌린다. 검사가 마감 일관성을 확인한다.

### 7단계. RESUME 다시 쓰기

RESUME는 덧붙이지 말고 **통째로 다시 쓴다.** 한 화면 안에 다음 다섯 항목만 둔다: 현재 위치, 마감 상태와 현금, 이달 합의된 것, 미결 질문, 다음 행동. 과거 경위는 `records.changes`와 git 이력에 있다.

### 8단계. 게시 (D036: 합의한 변경을 구현·검증했으면 매번)

1. `main`: second-life의 변경 파일만 커밋한다(다른 프로젝트 변경을 섞지 않는다). 메시지 끝에 지정된 Co-Authored-By 줄을 단다. `git push origin main`.
2. `gh-pages`: 변경된 **공개 파일만** 같은 경로로 올린다. 대상은 `series/investing/dashboard.html`, 바뀌었으면 `characters/person-NNN.html`과 그 페이지가 쓰는 이미지다. 작업 폴더를 바꾸지 않고 임시 인덱스로 커밋한다.
   ```
   cd <저장소 루트>; git fetch origin gh-pages
   export GIT_INDEX_FILE=$(mktemp); git read-tree origin/gh-pages
   h=$(git hash-object -w second-life/series/investing/dashboard.html)
   git update-index --add --cacheinfo 100644,$h,series/investing/dashboard.html
   t=$(git write-tree); c=$(git commit-tree $t -p origin/gh-pages -m "Publish ...")
   git push origin "${c}:refs/heads/gh-pages"; unset GIT_INDEX_FILE
   ```
   (zsh에서는 `$c:gh-pages`가 변수 수식어로 해석되므로 반드시 `${c}`로 감싼다.)
3. 확인: `gh api repos/dagan-and/novel/pages/builds/latest`의 상태가 built인지, 공개 URL이 HTTP 200인지, 내려받은 파일이 로컬 생성물과 같은지(SHA256) 본다. 공개 URL: `https://dagan-and.github.io/novel/series/investing/dashboard.html?month=YYYY-MM`
4. 보고할 때 로컬 수정, main 커밋·푸시, gh-pages 게시, 라이브 확인을 구분한다.
5. records·ledger·planning·research·인물 원본은 Pages에 올리지 않는다.

---

## 5. 돈 규칙 (`data/ledger.json`, 2026-11-19 사용자 확정)

| 규칙 | 내용 | 결정 |
| --- | --- | --- |
| 시작 현금 | 2005-01-01에 100,000원 | D041 |
| 용돈 | 월 100,000원. 첫 광고대금을 받은 달(5월)까지 받고 **6월부터 없음**. 남은 용돈은 현금으로 쌓인다 | D044 |
| 광고 지급 | 월말 미지급 잔액이 **100달러 이상이면 다음 달 말에 전액** 어머니 계좌로 들어온다. 첫 수령 5월 말 192달러(3~4월분), 이후 매달 받는다 | D042 |
| 분배 | 3월 발생분부터 모두 **용식 70%·어머니 30%**. 수령한 달에 원화 총액을 나눠 용식 몫은 바로 용식 현금 | D043 |
| 환율 | 수령 월의 **당시 월평균 실제 환율**(미국 연준 G.5). `rules.fx.krw_per_usd`에 월별로 적는다. 표시용 1달러≈1000원은 발생액 그래프에만 쓴다 | D046 |
| 수수료 | 사용자가 정하기 전까지 0 | D046 |
| 지출 | 1~6월은 채택한 예산표 합계(316,000원), 7~9월은 각 20만원. 앞으로도 월 총액 한 줄 | D045, D049, D052 |
| 비용 부담 | 사이트비·생활비는 용식 현금에서 나간다. 어머니 몫에서 다시 빼지 않는다 | D028, D044 |
| 총자산 | 현금 + 투자 평가액 + 기록된 소유 자산. 미수령 광고·가족 자산·예산 잔여는 넣지 않는다 | D039 |

계산 순서(월마다): ① 이달 말 수령(지난달 말 잔액이 기준 이상일 때) → ② 용돈 → ③ 지출 → ④ 월말 미지급 잔액과 다음 달 지급 예정액. 이 계산은 `scripts/cashflow.py` 한 곳에 있다.

새 달에 할 일:
- 그달 환율을 `rules.fx.krw_per_usd`에 추가한다.
- 그달 총지출을 `spending`에 한 줄로 넣는다(대략적인 금액).
- 규칙이 바뀌면 rules를 고치고 결정 D와 변경 C를 남긴다.

마감 잔액(참고): 1월 137,500원 → 2월 192,000원 → 3월 246,500원 → 4월 306,000원 → 5월 494,647원 → 6월 604,687원 → 7월 703,994원 → 8월 807,944원 → **9월 1,076,521원(마감)**.

### 5-1. 사이트 유입과 활성화 (D050·D051)

- **선형으로 늘리지 않는다.** 월 PV는 섹션별(디아2·WoW·새 게임) PV의 합이다. 섹션 PV는 다음을 곱해 정한다.
  - 그 게임의 인기 흐름: 디아2는 하락, WoW는 상승, 새 게임은 섹션을 연 달부터
  - 계절: 방학이면 늘고 시험기간이면 줄어든다
  - 이벤트: 패치, 확장팩 발표, 래더 초기화
  - 사이트 평판
- 근거는 그달 시대 조사(`research/monthly/`)의 확인된 사실에서 가져온다.
- 7~9월 기준값(PV): 7월 34만(디아2 17·WoW 17), 8월 52만(29·23, 1.11 래더 초기화), 9월 38만(16·22, 개학).
- 활성화 단계는 `metrics.site_activity_stages`를 기준으로 refresh가 일평균 방문자로 계산한다(`monthly[].activity_stage`).
  - 1 초기: 300명 미만
  - 2 단골 형성: 300명~
  - 3 활성 커뮤니티: 1,500명~
  - 4 대형: 5,000명~
- 단계가 바뀌는 달에는 운영진 모집, 호스팅 업그레이드 같은 사건을 제안서에 올린다. 2005년 5~9월은 3단계다.
- 새 게임 섹션을 추가하면 `section_pageviews`에 키를 더한다(예: `dnf`). 현황판 문구는 `scripts/templates/dashboard.html`의 siteActivity 부분에서 함께 고친다.

---

### 5-2. 화면·서술·성적 후속 규칙 (D059~D062)

- 공개 현황판에는 사이트 일별 변화·하루의 운영 지표·누적 광고 발생액 차트를 표시하지 않는다. 월별 수익·방문 표와 광고 정산은 유지한다. 내부 모형 배분 데이터가 있어도 서버 로그로 부르거나 제거한 차트를 다시 추가하지 않는다.
- 월간 본문을 진행할 때 섹션별 유입과 광고 발생액의 모형을 함께 검토한다. 누락된 채로 게시하지 않으며, 조사 불가와 아직 산정하지 않음을 구분한다. 창작 추정은 실측이나 사용자가 지정한 숫자로 가장하지 않는다. 발생액을 같은 달 현금에 더하지 않는다.
- 사이트는 자동 일상 운영을 짧게 요약한다. 중요한 변화·장애·정산이 있을 때만 비중을 늘리고 수집기·게시판 기능을 매달 재설명하지 않는다. 기존 운영은 지속한다. 측정 없는 자동화율·절약시간을 생성하지 않는다.
- 성적은 원점수와 석차9등급을 구분한다. 내신 등급은 과목별 수강자 석차와 동점자·학기 성적 기준이 필요하다. 전체 평균·종합 전교1등만으로 모든 과목을1등급 처리하지 않는다. 전국연합은 당시 영역별 상대평가 기준을 적용하며 영어 절대평가나 현재 한국사 시험을 소급하지 않는다.
- 전국연합 점수안·예상 등급과 역사적으로 확인된 시험 구성·확정 등급컷을 구별한다. 응시 인원·누적 도수 없이 정밀 전국석차·백분위를 계산하지 않는다.11월 조사와 미채택 점수안은research/school/2005-11-mock.md 및 모형JSON에서 시작한다.

---

## 6. 자주 하는 실수

- RESUME에 날짜별 섹션을 덧붙이기 → 통째로 다시 쓴다.
- 본문에 "N달러 수령"이라고 쓰기 → 렌더러가 1000원 환율로 바꿔 장부와 달라진다. 원화로 쓴다.
- 같은 금액을 planning·README·RESUME·본문에 반복해서 적기 → 원본(ledger/metrics)과 본문에만 둔다.
- 예산(계획)을 실제 지출처럼 현금에서 빼기 → 실제 지출은 `ledger.spending`에만 쓴다.
- 미확인 날짜를 사실처럼 쓰기 → "10월 중순" 같은 범위로 쓰거나 사용자에게 확인한다.
- 다른 작품(`reunion`, `wish-*` 등)의 김용식 설정을 가져오기.
- 저장소 루트의 다른 프로젝트 변경까지 커밋하기.

---

## 7. 미결로 남아 있는 큰 항목 (2026-11-19 기준)

- 10·11월 마감 여부,11월 전국연합 확정 등급컷·응시자 분포,12월 구성
- 미성년 증권계좌 개설 요건(2005년)
- 풍덕고 실제 시험 일정
- 광고 수령 수수료(현재 0)

진행 상황은 RESUME에서 갱신한다.
