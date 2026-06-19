# 관계망 필터 UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `관계망.md`에 `타입:` 필드를 추가하고, `convert_setting.py`의 렌더러를 수정해 타입 탭(동맹/긴장/탐색/우정) + 인물 칩 필터 UI가 `python publish.py`로 자동 생성되게 한다.

**Architecture:** `관계망.md`에 데이터(타입)를 추가하고, `convert_setting.py`의 `render_kangemang()`이 이를 읽어 필터 UI + 타입 뱃지가 포함된 HTML을 생성한다. JS 필터 로직은 인라인으로 삽입. `publish.py`는 변경 없음.

**Tech Stack:** Python 3, 순수 HTML/CSS/JS (의존성 없음)

---

### Task 1: `관계망.md`에 타입 필드 추가

**Files:**
- Modify: `reunion/관계망.md`

타입 분류 (19쌍):
- **동맹**: 임소율×이하은, 임소율×한서진, 이하은×한서진, 이하은×정다온, 한서진×정다온
- **긴장**: 임소율×배수인, 임소율×정다온, 한서진×박미현, 임소율×박미현, 정다온×박미현
- **우정**: 이하은×오연서, 한서진×오연서
- **탐색**: 이하은×배수인, 박미현×오연서, 한서진×배수인, 정다온×배수인, 박미현×배수인

각 `### X × Y` 섹션의 첫 번째 불릿으로 `- 타입: 동맹` (또는 긴장/탐색/우정) 추가.

- [ ] **Step 1: 각 관계 섹션에 타입 불릿 추가**

`관계망.md`의 각 `### 이름 × 이름` 섹션에 다음 형식으로 첫 줄 추가:
```markdown
### 임소율 × 이하은
- 타입: 동맹
- 현재: ...
```

- [ ] **Step 2: 확인**

```bash
grep "타입:" reunion/관계망.md | wc -l
```
Expected: `19`

---

### Task 2: `convert_setting.py` — CSS 업데이트

**Files:**
- Modify: `reunion/convert_setting.py` (`KANGEMANG_CSS` 상수)

- [ ] **Step 1: `KANGEMANG_CSS`에 필터 UI + 타입 뱃지 CSS 추가**

`KANGEMANG_CSS = GAME_CSS_BASE + """` 블록 안에 기존 스타일 뒤에 아래 추가:

```css
    /* ── 필터 UI ── */
    .filter-bar { margin-bottom:1.2rem; }
    .type-tabs { display:flex; gap:0; border-bottom:1px solid var(--border); margin-bottom:0.75rem; overflow-x:auto; }
    .type-tab {
      padding:0.45rem 1rem; border:none; border-bottom:2px solid transparent;
      background:transparent; color:var(--text2); font-size:0.72rem;
      cursor:pointer; white-space:nowrap; letter-spacing:0.05em;
      font-family:inherit; transition:color 0.15s;
    }
    .type-tab:hover { color:var(--text); }
    .type-tab.active { border-bottom-color:var(--pink); color:var(--pink); }
    .char-chips { display:flex; gap:0.35rem; flex-wrap:wrap; align-items:center; }
    .chip-label { font-size:0.65rem; color:var(--text3); letter-spacing:0.05em; margin-right:0.2rem; }
    .char-chip-btn {
      padding:0.18rem 0.6rem; border-radius:12px; border:1px solid var(--border);
      background:rgba(42,34,96,0.3); color:var(--text2); font-size:0.68rem;
      cursor:pointer; font-family:inherit; transition:all 0.15s;
    }
    .char-chip-btn:hover { border-color:var(--border-hi); color:var(--text); }
    .char-chip-btn.active { border-color:var(--pink); background:rgba(192,80,168,0.15); color:var(--pink); }
    /* ── 관계 카드 (타입별 테두리) ── */
    .rel-card { background:var(--panel); border:1px solid var(--border); border-radius:8px; padding:1rem 1.2rem; transition:border-color 0.2s; border-left-width:3px; }
    .rel-card:hover { border-color:var(--border-hi); }
    .rel-card[data-type="동맹"] { border-left-color:#30a860; }
    .rel-card[data-type="긴장"] { border-left-color:#c07828; }
    .rel-card[data-type="탐색"] { border-left-color:#4080d0; }
    .rel-card[data-type="우정"] { border-left-color:#40b0c0; }
    .rel-card.hidden { display:none; }
    /* ── 타입 뱃지 ── */
    .type-badge { font-size:0.62rem; padding:0.12rem 0.5rem; border-radius:10px; white-space:nowrap; font-weight:500; }
    .badge-동맹 { background:rgba(48,168,96,0.15);  border:1px solid rgba(48,168,96,0.4);  color:#40c060; }
    .badge-긴장 { background:rgba(192,120,40,0.15); border:1px solid rgba(192,120,40,0.4); color:#e09040; }
    .badge-탐색 { background:rgba(64,128,208,0.15); border:1px solid rgba(64,128,208,0.4); color:#60a8e0; }
    .badge-우정 { background:rgba(64,176,192,0.15); border:1px solid rgba(64,176,192,0.4); color:#40b0c0; }
    /* ── 범례 ── */
    .type-legend { display:flex; gap:0.9rem; flex-wrap:wrap; margin-top:1rem; }
    .legend-entry { display:flex; align-items:center; gap:0.3rem; font-size:0.65rem; color:var(--text3); }
    .legend-bar { width:3px; height:12px; border-radius:2px; }
```

- [ ] **Step 2: 기존 `.rel-card`, `.rel-grid` 정의 제거**

`KANGEMANG_CSS`에서 아래 두 줄 삭제 (위 Step 1에서 재정의함):
```css
    .rel-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); gap:0.8rem; }
    .rel-card { background:var(--panel); border:1px solid var(--border); border-radius:8px; padding:1rem 1.2rem; transition:border-color 0.2s; }
    .rel-card:hover { border-color:var(--border-hi); }
```

---

### Task 3: `render_kangemang()` — 타입 파싱 + 필터 UI 생성

**Files:**
- Modify: `reunion/convert_setting.py` (`render_kangemang` 함수)

- [ ] **Step 1: 관계 섹션 파싱에서 타입 추출**

`render_kangemang()` 안의 rel_cards 생성 루프에서 `parse_bullets_to_dict(body)`로 파싱 후:
```python
rel_type = bul.get('타입', '')
```

- [ ] **Step 2: rel-card HTML에 `data-type` / `data-chars` 속성 + 타입 뱃지 추가**

기존 rel-card 템플릿을 아래로 교체:
```python
chars_attr = f'{given_name(n1)},{given_name(n2)}'
rel_cards.append(f'''
    <div class="rel-card" data-type="{rel_type}" data-chars="{chars_attr}">
      <div class="rel-pair-header">
        <div style="display:flex;align-items:center;gap:0.5rem;flex:1">
          <div class="rel-avatar-sm" style="background:{c1}">{given_name(n1)}</div>
          <div class="rel-vs">×</div>
          <div class="rel-avatar-sm" style="background:{c2}">{given_name(n2)}</div>
          <div class="rel-pair-name">{n1} × {n2}</div>
        </div>
        <span class="type-badge badge-{rel_type}">{rel_type}</span>
      </div>
      <div class="rel-section">
        <div class="rel-section-label">현재</div>
        <div class="rel-section-text">{current}</div>
      </div>
      <div class="rel-section">
        <div class="rel-section-label">최근 변화</div>
        <div class="rel-section-text">{recent}</div>
      </div>
      <div class="rel-honorifics">{hons}</div>
    </div>''')
```

- [ ] **Step 3: 필터 UI HTML 생성 함수 추가**

`render_kangemang()` 내에서 `rel_html` 생성 전에 타입/인물 목록 수집:
```python
types_order = ['동맹', '긴장', '탐색', '우정']
type_counts = {t: 0 for t in types_order}
all_chars = []
for title, body in rel_subsections:
    nm = re.match(r'(.+?)\s*[×x]\s*(.+)', title)
    if not nm:
        continue
    bul = parse_bullets_to_dict(body)
    t = bul.get('타입', '')
    if t in type_counts:
        type_counts[t] += 1
    for name in [nm.group(1).strip(), nm.group(2).strip()]:
        gn = given_name(name)
        if gn not in all_chars:
            all_chars.append(gn)

total = sum(type_counts.values())
type_tabs = f'<button class="type-tab active" data-type="all" onclick="filterRel(this,\'all\')">전체 ({total})</button>'
for t in types_order:
    if type_counts[t]:
        type_tabs += f'<button class="type-tab" data-type="{t}" onclick="filterRel(this,\'{t}\')">{t} ({type_counts[t]})</button>'

char_chips = '<span class="chip-label">인물</span>'
char_chips += '<button class="char-chip-btn active" data-char="all" onclick="filterChar(this,\'all\')">전체</button>'
for ch in all_chars:
    char_chips += f'<button class="char-chip-btn" data-char="{ch}" onclick="filterChar(this,\'{ch}\')">{ch}</button>'

filter_html = f'''  <div class="filter-bar">
    <div class="type-tabs">{type_tabs}</div>
    <div class="char-chips">{char_chips}</div>
  </div>'''
```

- [ ] **Step 4: JS 필터 로직 + 범례 포함한 `rel_html` 조합**

```python
filter_js = '''<script>
var _type = "all", _char = "all";
function filterRel(btn, t) {
  _type = t;
  document.querySelectorAll(".type-tab").forEach(function(b){
    b.classList.toggle("active", b.dataset.type === t);
  });
  applyFilter();
}
function filterChar(btn, c) {
  _char = c;
  document.querySelectorAll(".char-chip-btn").forEach(function(b){
    b.classList.toggle("active", b.dataset.char === c);
  });
  applyFilter();
}
function applyFilter() {
  document.querySelectorAll(".rel-card").forEach(function(card){
    var tm = _type === "all" || card.dataset.type === _type;
    var cm = _char === "all" || card.dataset.chars.split(",").indexOf(_char) !== -1;
    card.classList.toggle("hidden", !(tm && cm));
  });
}
</script>'''

legend_html = '''  <div class="type-legend">
    <div class="legend-entry"><div class="legend-bar" style="background:#30a860"></div>동맹</div>
    <div class="legend-entry"><div class="legend-bar" style="background:#c07828"></div>긴장</div>
    <div class="legend-entry"><div class="legend-bar" style="background:#4080d0"></div>탐색</div>
    <div class="legend-entry"><div class="legend-bar" style="background:#40b0c0"></div>우정</div>
  </div>'''

rel_html = f'{filter_html}\n  <div class="rel-grid">{"".join(rel_cards)}\n  </div>\n{legend_html}\n{filter_js}'
```

---

### Task 4: 테스트 실행 및 검증

**Files:**
- Run: `reunion/convert_setting.py`

- [ ] **Step 1: 단독 실행으로 HTML 생성**

```bash
cd /Users/kys1207/novel-repo/reunion && python3 convert_setting.py
```
Expected: `✓ html/setting/관계망.html 생성 완료`

- [ ] **Step 2: 출력 파일 기본 검증**

```bash
grep -c 'data-type=' reunion/html/setting/관계망.html
```
Expected: 19 이상 (각 rel-card마다 1개)

```bash
grep 'type-tab' reunion/html/setting/관계망.html | head -3
```
Expected: 탭 버튼 HTML 출력

- [ ] **Step 3: 브라우저 확인**

`reunion/html/setting/관계망.html` 파일을 브라우저로 열어 확인:
- 타입 탭 클릭 → 해당 타입 카드만 표시
- 인물 칩 클릭 → 해당 인물 포함 카드만 표시
- 탭 + 칩 동시 선택 → AND 필터 동작

---

### Task 5: `publish.py` 전체 파이프라인 확인

- [ ] **Step 1: dry run**

```bash
cd /Users/kys1207/novel-repo/reunion && python3 publish.py --dry
```
Expected: 에러 없이 완료, `html/setting/관계망.html` 갱신

- [ ] **Step 2: 완료 후 git 확인**

```bash
git diff --stat
```
Expected: `관계망.md`, `convert_setting.py`, `html/setting/관계망.html` 변경
