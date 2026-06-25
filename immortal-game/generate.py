#!/usr/bin/env python3
"""
불사자의 연대기 — 현황판 생성기
game-state.json + events.json + tech-tree.json → chronicle.html
"""

import argparse
import json
import re
import subprocess
import webbrowser
from pathlib import Path
from html import escape

BASE = Path(__file__).parent
PUBLISH_FILES = [
    "game-state.json",
    "events.json",
    "tech-tree.json",
    "chronicle.md",
    "chronicle.html",
    "tech-tree.md",
    "RESUME.md",
    ".gitignore",
    "generate.py",
    "tests/test_generate_git.py",
]


def load(filename):
    p = BASE / filename
    if not p.exists():
        print(f"[경고] {filename} 없음 — 기본값 사용")
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def stars(n, total=5):
    return (
        f'<span style="color:#C8A84B">{"★" * n}</span>'
        f'<span style="color:#2A3448">{"★" * (total - n)}</span>'
    )


def tech_dot(status):
    colors = {"done": "#4E8A65", "active": "#C8A84B", "available": "#2A3448", "locked": "#1A2535"}
    border = {"done": "#4E8A65", "active": "#C8A84B", "available": "#4A5568", "locked": "#2A3448"}
    c = colors.get(status, "#2A3448")
    b = border.get(status, "#2A3448")
    return f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{c};border:1px solid {b};margin-right:8px;vertical-align:middle"></span>'


def event_type_color(t):
    return {"social": "#4E8A65", "war": "#8A4E4E", "tech": "#4E7A8A",
            "political": "#C8A84B", "economic": "#7A6530"}.get(t, "#4A5568")


def build_relationships(state):
    rels = state.get("key_relationships", [])
    if not rels:
        return "<p style='color:#7A8898;font-size:12px'>없음</p>"
    items = []
    for r in rels:
        items.append(f"""
        <div style="padding:8px 10px;background:#1C2535;border-radius:4px;margin-bottom:6px">
          <div style="font-weight:700;color:#EDE5CF;font-size:13px">{escape(r.get('name',''))}</div>
          <div style="color:#C09840;font-size:11px">{escape(r.get('role',''))}</div>
          <div style="color:#A8BAC8;font-size:12px;margin-top:2px">{escape(r.get('status',''))}</div>
        </div>""")
    return "".join(items)


def build_military(state):
    mil = state.get("military", [])
    if not mil:
        return "<p style='color:#7A8898;font-size:12px'>없음</p>"
    items = []
    for m in mil:
        items.append(f"""
        <div style="padding:8px 10px;background:#1C2535;border-radius:4px;margin-bottom:6px;border-left:3px solid #8A4E4E">
          <div style="font-weight:700;color:#EDE5CF;font-size:13px">{escape(m.get('name',''))}</div>
          <div style="color:#C8A84B;font-size:12px;margin-top:2px">{m.get('size', 0)}명 · {escape(m.get('status',''))}</div>
          <div style="color:#A8BAC8;font-size:11px;margin-top:2px">{escape(m.get('equipment',''))}</div>
          <div style="color:#C09840;font-size:11px;margin-top:1px">지휘: {escape(m.get('commander',''))}</div>
        </div>""")
    return "".join(items)


def build_threats(state):
    threats = state.get("threats", [])
    if not threats:
        return "<p style='color:#7A8898;font-size:12px'>없음</p>"
    level_color = {"위험": "#8A4E4E", "경계": "#C8A84B", "안전": "#4E8A65"}
    items = []
    for t in threats:
        color = level_color.get(t.get("level", ""), "#4A5568")
        items.append(f"""
        <div style="padding:7px 10px;background:#1C2535;border-radius:4px;margin-bottom:6px;border-left:3px solid {color}">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <span style="font-weight:700;color:#EDE5CF;font-size:13px">{escape(t.get('name',''))}</span>
            <span style="font-size:10px;color:{color};font-weight:700;letter-spacing:.05em">{escape(t.get('level',''))}</span>
          </div>
          <div style="color:#A8BAC8;font-size:11px;margin-top:3px">{escape(t.get('reason',''))}</div>
        </div>""")
    return "".join(items)


def build_assets(state):
    assets = state.get("assets", [])
    if not assets:
        return "<p style='color:#7A8898;font-size:12px'>없음</p>"
    items = []
    for a in assets:
        items.append(f"""
        <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #2A3448;font-size:12px">
          <span style="color:#A8BAC8">{escape(a.get('name',''))}</span>
          <span style="color:#EDE5CF;font-weight:600">{a.get('count','')}척 · {escape(a.get('status',''))}</span>
        </div>""")
    return "".join(items)


def build_tech_item(t):
    status = t.get("status", "locked")
    name = escape(t.get("name", ""))
    spread = t.get("spread_rate", 0)
    yr = t.get("introduced_year")
    effect = t.get("effect", "")
    label_color = {"done": "#EDE5CF", "active": "#C8A84B", "available": "#B0C4D4", "locked": "#6A7A8A"}.get(status, "#6A7A8A")
    spread_bar = ""
    if status in ("done", "active") and spread > 0:
        bar_color = "#4E8A65" if status == "done" else "#C8A84B"
        spread_bar = f'<div style="height:2px;background:#2A3448;border-radius:1px;margin-top:4px"><div style="height:2px;background:{bar_color};width:{spread}%;border-radius:1px"></div></div>'
    yr_text = f" <span style='color:#7A8898;font-size:10px'>AD {yr}</span>" if yr else ""
    effect_text = f'<div style="color:#7A8898;font-size:10px;padding-left:16px">{escape(effect)}</div>' if effect and status != "locked" else ""
    return f"""
    <div style="padding:6px 0;border-bottom:1px solid #1C2535">
      <div style="display:flex;align-items:center">
        {tech_dot(status)}
        <span style="font-size:13px;color:{label_color}">{name}{yr_text}</span>
      </div>
      {effect_text}
      {spread_bar}
    </div>"""


def build_tech_tabs(techs):
    categories = {}
    cat_order = []
    for t in techs:
        cat = t.get("category", "기타")
        if cat not in categories:
            categories[cat] = []
            cat_order.append(cat)
        categories[cat].append(t)

    status_counts = {}
    for cat in cat_order:
        done = sum(1 for t in categories[cat] if t.get("status") == "done")
        active = sum(1 for t in categories[cat] if t.get("status") == "active")
        total = len(categories[cat])
        status_counts[cat] = (done, active, total)

    btn_html = []
    panel_html = []
    for i, cat in enumerate(cat_order):
        done, active, total = status_counts[cat]
        is_first = (i == 0)
        safe_id = f"tech-{cat}"
        badge_color = "#4E8A65" if done > 0 else "#C8A84B" if active > 0 else "#4A5568"
        badge = f'<span style="font-size:9px;background:{badge_color};color:#0D1117;border-radius:2px;padding:1px 5px;margin-left:6px;font-weight:700">{done}/{total}</span>'
        btn_html.append(
            f'<button class="sub-tab-btn{"  sub-active" if is_first else ""}" '
            f'onclick="switchSubTab(\'{safe_id}\', this)">'
            f'{escape(cat)}{badge}</button>'
        )
        items_html = "".join(build_tech_item(t) for t in categories[cat])
        panel_html.append(
            f'<div id="{safe_id}" class="sub-tab-panel{"  sub-active" if is_first else ""}">'
            f'{items_html}</div>'
        )

    return f"""
<div style="border-bottom:1px solid #2A3448;margin-bottom:16px;display:flex;flex-wrap:wrap;gap:2px">
  {"".join(btn_html)}
</div>
{"".join(panel_html)}"""


def build_tech_rows(techs):
    categories = {}
    for t in techs:
        cat = t.get("category", "기타")
        categories.setdefault(cat, []).append(t)

    rows = []
    for cat, items in categories.items():
        rows.append(f'<div style="color:#C09840;font-size:10px;letter-spacing:.15em;text-transform:uppercase;margin:10px 0 4px">{escape(cat)}</div>')
        for t in items:
            rows.append(build_tech_item(t))
    return "".join(rows)


def parse_equipment_list(eq_str):
    """'A 12 + B 34정 + C' 형식 문자열을 [(이름, 수량|None)] 목록으로 변환."""
    result = []
    for part in eq_str.split("+"):
        part = part.strip()
        if not part:
            continue
        m = re.search(r"(\d[\d,]*)\s*([정기척개명]?)$", part)
        if m:
            count = int(m.group(1).replace(",", ""))
            name = part[: m.start()].strip()
            result.append((name, count))
        else:
            result.append((part, None))
    return result


def build_stockpile(state):
    mil = state.get("military", [])
    assets = state.get("assets", [])

    # 병기: 수량이 있는 항목만
    eq_with = []
    eq_misc = []
    for unit in mil:
        for name, count in parse_equipment_list(unit.get("equipment", "")):
            if count is not None:
                eq_with.append((name, count))
            else:
                eq_misc.append(name)

    eq_rows = "".join(
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
        f'padding:7px 0;border-bottom:1px solid #1C2535">'
        f'<span style="color:#C8D8E8;font-size:13px">{escape(n)}</span>'
        f'<span style="color:#EDE5CF;font-weight:700;font-size:14px">{c:,}</span></div>'
        for n, c in eq_with
    )
    if eq_misc:
        eq_rows += (
            f'<div style="padding:7px 0;font-size:11px;color:#8A9AB0;font-style:italic">'
            f'기타: {escape(" · ".join(eq_misc))}</div>'
        )

    # 원자재 비축 (assets 중 숫자가 큰 물자류)
    MATERIAL_KEYWORDS = ["비축", "원석", "광석", "석탄", "철광", "탄층"]
    mat_assets = [a for a in assets if any(k in a.get("name", "") for k in MATERIAL_KEYWORDS)]
    mat_rows = "".join(
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
        f'padding:7px 0;border-bottom:1px solid #1C2535">'
        f'<span style="color:#C8D8E8;font-size:13px">{escape(a.get("name",""))}</span>'
        f'<span style="color:#C8A84B;font-weight:700;font-size:14px">{a.get("count",0):,}</span></div>'
        for a in mat_assets
    )

    no_item = "<p style='color:#8A9AB0;font-size:12px;padding:8px 0'>없음</p>"
    return f"""
<div style="margin-bottom:20px">
  <div style="font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:#C09840;margin-bottom:8px;padding-bottom:4px;border-bottom:1px solid #2A3448">⚔ 병기 현황</div>
  {eq_rows or no_item}
</div>
<div>
  <div style="font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:#C09840;margin-bottom:8px;padding-bottom:4px;border-bottom:1px solid #2A3448">🪨 원자재 비축</div>
  {mat_rows or no_item}
</div>"""


def nl2br(text):
    return escape(text).replace("\n\n", "</p><p style='margin-top:10px'>").replace("\n", "<br>")


def build_events(events):
    if not events:
        return "<p style='color:#7A8898'>기록 없음</p>"

    reversed_events = list(reversed(events))
    items = []
    for i, e in enumerate(reversed_events):
        yr = f"{'AD' if e.get('era','AD')=='AD' else 'BC'} {e.get('year','')}년"
        is_latest = (i == 0)
        dot_style = (
            "width:10px;height:10px;background:#C8A84B;border:1px solid #C8A84B;box-shadow:0 0 8px #C8A84B44"
            if is_latest else
            "width:8px;height:8px;background:#7A6530;border:1px solid #C8A84B"
        )

        narrative = e.get("narrative", e.get("body", ""))
        world = e.get("world", "")
        result = e.get("result", "")
        etype = e.get("type", "")
        type_color = event_type_color(etype)

        narrative_html = f'<p style="color:#A8BAC8;font-size:13px;line-height:1.8">{nl2br(narrative)}</p>' if narrative else ""

        world_html = (
            f'<div style="margin-top:10px;padding:7px 10px;background:#0D1117;border-left:2px solid #4A5568;font-size:12px;color:#8A9AB0;font-style:italic">'
            f'🌍 {escape(world)}</div>'
        ) if world else ""

        result_html = (
            f'<div style="margin-top:8px;padding:5px 10px;background:#1C2535;border-left:2px solid #4E8A65;font-size:12px;color:#EDE5CF">'
            f'→ {escape(result)}</div>'
        ) if result else ""

        type_badge = (
            f'<span style="font-size:9px;letter-spacing:.1em;color:{type_color};border:1px solid {type_color};'
            f'border-radius:2px;padding:1px 5px;margin-left:8px;vertical-align:middle">{escape(etype.upper())}</span>'
        ) if etype else ""

        latest_badge = '<span style="font-size:9px;background:#C8A84B;color:#0D1117;border-radius:2px;padding:1px 6px;margin-left:6px;font-weight:700;vertical-align:middle">최신</span>' if is_latest else ""

        items.append(f"""
        <div style="position:relative;padding-left:28px;margin-bottom:36px">
          <div style="position:absolute;left:-5px;top:5px;{dot_style};border-radius:50%"></div>
          <div style="font-size:11px;letter-spacing:.14em;color:#C8A84B;font-weight:700;margin-bottom:4px">{yr}{latest_badge}</div>
          <div style="font-size:15px;font-weight:700;color:#EDE5CF;margin-bottom:8px">{escape(e.get('title',''))}{type_badge}</div>
          {narrative_html}
          {world_html}
          {result_html}
        </div>""")

    return "".join(items)


def build_current_card(state):
    yr = state.get("year", "?")
    era = state.get("era", "AD")
    situation = escape(state.get("current_situation", ""))
    world = escape(state.get("world_summary", ""))
    sit_html = f'<div style="margin-top:10px;padding:8px 10px;background:#1C2535;border-left:2px solid #8A4E4E;font-size:12px;color:#EDE5CF">⚠ {situation}</div>' if situation else ""
    world_html = f'<div style="margin-top:8px;padding:8px 10px;background:#1C2535;border-left:2px solid #4A5568;font-size:12px;color:#8A9AB0;font-style:italic">🌍 {world}</div>' if world else ""
    return f"""
    <div style="background:#141B26;border:1px solid #7A6530;border-radius:4px;padding:16px 20px;margin-bottom:32px">
      <div style="font-size:10px;letter-spacing:.2em;color:#C8A84B;text-transform:uppercase;margin-bottom:8px">현재</div>
      <div style="font-size:36px;font-weight:700;color:#EDE5CF;line-height:1;font-variant-numeric:tabular-nums">{era} {yr}</div>
      <div style="color:#A8BAC8;font-size:12px;margin-top:4px">{escape(state.get('identity',{}).get('location',''))}</div>
      {sit_html}
      {world_html}
    </div>"""


def build_territory_map(state):
    controlled = state.get("stats", {}).get("controlled_territory", 0)
    location = escape(state.get("identity", {}).get("location", "영산강·목포 해안권"))
    lines = [
        "                          [북 / 내륙]",
        "",
        "                  사로           진목",
        "                    \\             /",
        "                     \\           /",
        "                      \\         /",
        "                       \\       /",
        "                        구야",
        "                         |",
        "                         |",
        "                을지 영향권/완충지대",
        "                         |",
        "                         |",
        "        비리(상류) ---- 영산 본진 ---- 해루(강어귀/북쪽 수로)",
        "                         |",
        "                         |",
        "                    해촌 / 항만 핵심",
        "                         |",
        "                    염포(서쪽 연안)",
        "                         |",
        "                    목포 해안 / 바다",
        "",
        "                          [남 / 해안]",
    ]
    legend = [
        ("직할 중심", "영산 본진, 목포 해안"),
        ("내륙 축", "비리, 구야, 사로, 진목"),
        ("연안 축", "해촌, 해루, 염포"),
        ("완충권", "을지 영향권"),
    ]
    legend_html = "".join(
        f"""
        <div style="padding:8px 10px;background:#1C2535;border-radius:4px">
          <div style="font-size:11px;color:#C8A84B;font-weight:700;margin-bottom:2px">{escape(title)}</div>
          <div style="font-size:12px;color:#A8BAC8">{escape(body)}</div>
        </div>"""
        for title, body in legend
    )
    return f"""
    <section style="background:#141B26;border:1px solid #2A3448;border-radius:4px;padding:16px 20px;margin-bottom:32px">
      <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-end;flex-wrap:wrap;margin-bottom:12px">
        <div>
          <div style="font-size:10px;letter-spacing:.2em;color:#C8A84B;text-transform:uppercase;margin-bottom:6px">현재 판도</div>
          <div style="font-size:14px;color:#EDE5CF;font-weight:700">{location}</div>
        </div>
        <div style="font-size:12px;color:#A8BAC8">통제 영토 {controlled}권 기준 개략도</div>
      </div>
      <pre style="white-space:pre;overflow:auto;background:#0D1117;border:1px solid #2A3448;border-radius:4px;padding:14px 16px;color:#EDE5CF;font-size:12px;line-height:1.55;margin-bottom:12px">{escape(chr(10).join(lines))}</pre>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px">
        {legend_html}
      </div>
    </section>"""


def generate(state, events, techs):
    identity = state.get("identity", {})
    stats = state.get("stats", {})
    influence = stats.get("tribal_influence", 0)
    population = stats.get("population_under_influence", 0)
    turn = state.get("turn", 1)
    death_count = identity.get("death_count", 0)
    goal = escape(state.get("long_term_goal", ""))
    name = escape(identity.get("name", "금휘"))
    role = escape(identity.get("role", ""))
    location = escape(identity.get("location", ""))
    apparent_age = identity.get("apparent_age", "?")
    start_year = 1

    identity_rows = "".join(
        f'<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #2A3448;font-size:13px">'
        f'<span style="color:#A8BAC8">{k}</span>'
        f'<span style="font-weight:600;color:#EDE5CF">{v}</span></div>'
        for k, v in [("이름", name), ("신분", role), ("위치", location), ("겉나이", f"{apparent_age}세")]
    )

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>금휘의 연대기</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0D1117;color:#EDE5CF;font-family:"Apple SD Gothic Neo","Malgun Gothic","Noto Sans KR",sans-serif;font-size:14px;line-height:1.7;min-height:100vh}}
a{{color:#C8A84B}}
/* 메인 탭 */
.tab-btn{{
  background:none;border:none;color:#A0B0C0;font-family:inherit;font-size:13px;
  padding:11px 22px;cursor:pointer;border-bottom:2px solid transparent;
  letter-spacing:.05em;transition:color .15s;white-space:nowrap;
}}
.tab-btn:hover{{color:#EDE5CF}}
.tab-btn.active{{color:#C8A84B;border-bottom-color:#C8A84B;font-weight:600}}
.tab-panel{{display:none;padding:28px 32px;max-width:900px}}
.tab-panel.active{{display:block}}
/* 섹션 레이블 */
.section-label{{font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#C09840;margin-bottom:10px}}
/* 카드 */
.card{{background:#141B26;border:1px solid #2A3448;border-radius:6px;padding:18px 22px;margin-bottom:20px}}
/* 서브 탭 */
.sub-tab-btn{{
  background:none;border:none;color:#8A9AB0;font-family:inherit;font-size:12px;
  padding:8px 15px;cursor:pointer;border-bottom:2px solid transparent;
  letter-spacing:.04em;transition:color .12s;white-space:nowrap;
}}
.sub-tab-btn:hover{{color:#EDE5CF}}
.sub-tab-btn.sub-active{{color:#C8A84B;border-bottom-color:#C09840;font-weight:600}}
.sub-tab-panel{{display:none}}
.sub-tab-panel.sub-active{{display:block;padding-top:12px}}
/* 공통 행 */
.row{{display:flex;justify-content:space-between;align-items:baseline;padding:7px 0;border-bottom:1px solid #1E2A3A;font-size:13px}}
.row-label{{color:#A8B8C8}}
.row-value{{color:#EDE5CF;font-weight:600}}
</style>
</head>
<body>

<header style="border-bottom:1px solid #7A6530;padding:20px 32px 16px;display:flex;align-items:baseline;gap:20px;flex-wrap:wrap">
  <div>
    <div style="font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#C8A84B;margin-bottom:4px">불사자의 기록</div>
    <div style="display:flex;align-items:baseline;gap:12px">
      <span style="font-size:26px;font-weight:700;letter-spacing:.04em">{name}</span>
      <span style="font-size:14px;color:#C09840;letter-spacing:.1em">金煇</span>
    </div>
  </div>
  <div style="margin-left:auto;text-align:right;color:#A8BAC8;font-size:12px;line-height:2">
    <div>목표 &nbsp;<strong style="color:#C8A84B">{goal}</strong></div>
    <div>시작 <strong style="color:#C8A84B">AD {start_year}년</strong> &nbsp;·&nbsp; 현재 <strong style="color:#C8A84B">AD {state.get('year',1)}년</strong></div>
    <div>총 턴 <strong style="color:#C8A84B">{turn}</strong> &nbsp;·&nbsp; 사망 <strong style="color:#C8A84B">{death_count}</strong>회</div>
  </div>
</header>

<!-- 탭 바 -->
<nav style="border-bottom:1px solid #2A3448;padding:0 24px;display:flex;overflow-x:auto">
  <button class="tab-btn active" onclick="switchTab('현황', this)">현황</button>
  <button class="tab-btn" onclick="switchTab('군사위협', this)">군사·위협</button>
  <button class="tab-btn" onclick="switchTab('인물', this)">인물</button>
  <button class="tab-btn" onclick="switchTab('기술', this)">기술</button>
  <button class="tab-btn" onclick="switchTab('판도', this)">판도</button>
  <button class="tab-btn" onclick="switchTab('연대기', this)">연대기 ({len(events)})</button>
</nav>

<!-- 탭 1: 현황 -->
<div id="tab-현황" class="tab-panel active">
  {build_current_card(state)}

  <div class="card">
    <div class="section-label">현재 신분</div>
    {identity_rows}
  </div>

  <div class="card">
    <div class="section-label">세력 현황</div>
    <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #2A3448;font-size:13px">
      <span style="color:#A8BAC8">부족 영향력</span><span>{stars(influence)}</span>
    </div>
    <div style="display:flex;justify-content:space-between;padding:8px 0;font-size:13px">
      <span style="color:#A8BAC8">영향 인구</span><span style="font-weight:600">{population:,}명</span>
    </div>
  </div>
</div>

<!-- 탭 2: 군사·위협 -->
<div id="tab-군사위협" class="tab-panel">
  <div class="card">
    <div class="section-label">군사력</div>
    {build_military(state)}
  </div>

  <div class="card">
    <div class="section-label">위협</div>
    {build_threats(state)}
  </div>

  <div class="card">
    <div class="section-label">군수 비축량</div>
    {build_stockpile(state)}
  </div>

  <div class="card">
    <div class="section-label">기타 자산</div>
    {build_assets(state)}
  </div>
</div>

<!-- 탭 3: 인물 -->
<div id="tab-인물" class="tab-panel">
  <div class="card">
    <div class="section-label">주요 인물</div>
    {build_relationships(state)}
  </div>
</div>

<!-- 탭 4: 기술 -->
<div id="tab-기술" class="tab-panel">
  <div class="card">
    <div style="font-size:11px;color:#7A8898;margin-bottom:12px">
      <span style="color:#4E8A65">●</span> 완료 &nbsp;
      <span style="color:#C8A84B">●</span> 진행 &nbsp;
      <span style="color:#7A8898">●</span> 가능 &nbsp;
      <span style="color:#2A3448">●</span> 잠김
    </div>
    {build_tech_tabs(techs)}
  </div>
</div>

<!-- 탭 5: 판도 -->
<div id="tab-판도" class="tab-panel" style="max-width:780px">
  {build_territory_map(state)}
</div>

<!-- 탭 6: 연대기 -->
<div id="tab-연대기" class="tab-panel">
  <div style="font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:#C09840;margin-bottom:16px;padding-bottom:6px;border-bottom:1px solid #2A3448">연대기 (최신순)</div>
  <div style="position:relative;padding-left:24px;border-left:1px solid #2A3448">
    {build_events(events)}
  </div>
</div>

<script>
function switchTab(name, btn) {{
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  btn.classList.add('active');
}}
function switchSubTab(id, btn) {{
  var parent = btn.closest('.card');
  parent.querySelectorAll('.sub-tab-panel').forEach(p => p.classList.remove('sub-active'));
  parent.querySelectorAll('.sub-tab-btn').forEach(b => b.classList.remove('sub-active'));
  document.getElementById(id).classList.add('sub-active');
  btn.classList.add('sub-active');
}}
</script>
</body>
</html>"""


def run_git(cmd, **kwargs):
    return subprocess.run(
        ["git", *cmd],
        cwd=BASE,
        text=True,
        capture_output=True,
        **kwargs,
    )


def publish_to_git(files=PUBLISH_FILES, message=None, runner=run_git):
    allowed = set(files)
    staged = runner(["diff", "--cached", "--name-only"], check=True).stdout.splitlines()
    unexpected = [name for name in staged if name not in allowed]
    if unexpected:
        raise RuntimeError(
            "이미 Git에 올릴 준비가 된 다른 파일이 있어 자동 업로드를 멈췄습니다: "
            + ", ".join(unexpected)
        )

    runner(["add", "--", *files], check=True)
    diff = runner(["diff", "--cached", "--quiet"])
    if diff.returncode == 0:
        return "no changes"

    commit_message = message or "Update immortal game chronicle"
    runner(["commit", "-m", commit_message], check=True)
    runner(["push"], check=True)
    return "pushed"


def main():
    parser = argparse.ArgumentParser(description="불사자의 연대기 HTML 생성기")
    parser.add_argument("--no-open", action="store_true", help="생성 후 브라우저를 열지 않음")
    parser.add_argument("--no-git", action="store_true", help="Git 커밋/푸시를 하지 않음")
    parser.add_argument(
        "--message",
        default=None,
        help="자동 Git 커밋 메시지",
    )
    args = parser.parse_args()

    state = load("game-state.json") or {}
    events = load("events.json") or []
    techs = load("tech-tree.json") or []

    html = generate(state, events, techs)

    out = BASE / "chronicle.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✓ 생성 완료: {out}")
    if not args.no_git:
        try:
            result = publish_to_git(message=args.message)
            if result == "pushed":
                print("✓ Git 업로드 완료")
            else:
                print("✓ Git 변경 없음")
        except (RuntimeError, subprocess.CalledProcessError) as exc:
            print(f"✗ Git 업로드 실패: {exc}")
            raise SystemExit(1)

    if not args.no_open:
        webbrowser.open(out.as_uri())


if __name__ == "__main__":
    main()
