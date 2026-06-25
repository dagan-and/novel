#!/usr/bin/env python3
"""
불사자의 연대기 — 현황판 생성기
game-state.json + events.json + tech-tree.json → chronicle.html
"""

import argparse
import json
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
    "RESUME.md",
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
        return "<p style='color:#4A5568;font-size:12px'>없음</p>"
    items = []
    for r in rels:
        items.append(f"""
        <div style="padding:8px 10px;background:#1C2535;border-radius:4px;margin-bottom:6px">
          <div style="font-weight:700;color:#EDE5CF;font-size:13px">{escape(r.get('name',''))}</div>
          <div style="color:#7A6530;font-size:11px">{escape(r.get('role',''))}</div>
          <div style="color:#8A9BA8;font-size:12px;margin-top:2px">{escape(r.get('status',''))}</div>
        </div>""")
    return "".join(items)


def build_military(state):
    mil = state.get("military", [])
    if not mil:
        return "<p style='color:#4A5568;font-size:12px'>없음</p>"
    items = []
    for m in mil:
        items.append(f"""
        <div style="padding:8px 10px;background:#1C2535;border-radius:4px;margin-bottom:6px;border-left:3px solid #8A4E4E">
          <div style="font-weight:700;color:#EDE5CF;font-size:13px">{escape(m.get('name',''))}</div>
          <div style="color:#C8A84B;font-size:12px;margin-top:2px">{m.get('size', 0)}명 · {escape(m.get('status',''))}</div>
          <div style="color:#8A9BA8;font-size:11px;margin-top:2px">{escape(m.get('equipment',''))}</div>
          <div style="color:#7A6530;font-size:11px;margin-top:1px">지휘: {escape(m.get('commander',''))}</div>
        </div>""")
    return "".join(items)


def build_threats(state):
    threats = state.get("threats", [])
    if not threats:
        return "<p style='color:#4A5568;font-size:12px'>없음</p>"
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
          <div style="color:#8A9BA8;font-size:11px;margin-top:3px">{escape(t.get('reason',''))}</div>
        </div>""")
    return "".join(items)


def build_assets(state):
    assets = state.get("assets", [])
    if not assets:
        return "<p style='color:#4A5568;font-size:12px'>없음</p>"
    items = []
    for a in assets:
        items.append(f"""
        <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #2A3448;font-size:12px">
          <span style="color:#8A9BA8">{escape(a.get('name',''))}</span>
          <span style="color:#EDE5CF;font-weight:600">{a.get('count','')}척 · {escape(a.get('status',''))}</span>
        </div>""")
    return "".join(items)


def build_tech_rows(techs):
    categories = {}
    for t in techs:
        cat = t.get("category", "기타")
        categories.setdefault(cat, []).append(t)

    rows = []
    for cat, items in categories.items():
        rows.append(f'<div style="color:#7A6530;font-size:10px;letter-spacing:.15em;text-transform:uppercase;margin:10px 0 4px">{escape(cat)}</div>')
        for t in items:
            status = t.get("status", "locked")
            name = escape(t.get("name", ""))
            spread = t.get("spread_rate", 0)
            yr = t.get("introduced_year")
            effect = t.get("effect", "")

            label_color = {"done": "#EDE5CF", "active": "#C8A84B", "available": "#8A9BA8", "locked": "#3A4558"}.get(status, "#3A4558")
            spread_bar = ""
            if status in ("done", "active") and spread > 0:
                bar_color = "#4E8A65" if status == "done" else "#C8A84B"
                spread_bar = f'<div style="height:2px;background:#2A3448;border-radius:1px;margin-top:4px"><div style="height:2px;background:{bar_color};width:{spread}%;border-radius:1px"></div></div>'
            yr_text = f" <span style='color:#4A5568;font-size:10px'>AD {yr}</span>" if yr else ""
            effect_text = f'<div style="color:#4A5568;font-size:10px;padding-left:16px">{escape(effect)}</div>' if effect and status != "locked" else ""

            rows.append(f"""
            <div style="padding:3px 0">
              <div style="display:flex;align-items:center">
                {tech_dot(status)}
                <span style="font-size:12px;color:{label_color}">{name}{yr_text}</span>
              </div>
              {effect_text}
              {spread_bar}
            </div>""")
    return "".join(rows)


def nl2br(text):
    return escape(text).replace("\n\n", "</p><p style='margin-top:10px'>").replace("\n", "<br>")


def build_events(events):
    if not events:
        return "<p style='color:#4A5568'>기록 없음</p>"

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

        narrative_html = f'<p style="color:#8A9BA8;font-size:13px;line-height:1.8">{nl2br(narrative)}</p>' if narrative else ""

        world_html = (
            f'<div style="margin-top:10px;padding:7px 10px;background:#0D1117;border-left:2px solid #4A5568;font-size:12px;color:#6A7A8A;font-style:italic">'
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
    world_html = f'<div style="margin-top:8px;padding:8px 10px;background:#1C2535;border-left:2px solid #4A5568;font-size:12px;color:#6A7A8A;font-style:italic">🌍 {world}</div>' if world else ""
    return f"""
    <div style="background:#141B26;border:1px solid #7A6530;border-radius:4px;padding:16px 20px;margin-bottom:32px">
      <div style="font-size:10px;letter-spacing:.2em;color:#C8A84B;text-transform:uppercase;margin-bottom:8px">현재</div>
      <div style="font-size:36px;font-weight:700;color:#EDE5CF;line-height:1;font-variant-numeric:tabular-nums">{era} {yr}</div>
      <div style="color:#8A9BA8;font-size:12px;margin-top:4px">{escape(state.get('identity',{}).get('location',''))}</div>
      {sit_html}
      {world_html}
    </div>"""


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
</style>
</head>
<body>

<!-- 헤더 -->
<header style="border-bottom:1px solid #7A6530;padding:24px 32px 18px;display:flex;align-items:baseline;gap:20px;flex-wrap:wrap">
  <div>
    <div style="font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#C8A84B;margin-bottom:4px">불사자의 기록</div>
    <div style="display:flex;align-items:baseline;gap:12px">
      <span style="font-size:28px;font-weight:700;letter-spacing:.04em">{name}</span>
      <span style="font-size:15px;color:#7A6530;letter-spacing:.1em">金煇</span>
    </div>
  </div>
  <div style="margin-left:auto;text-align:right;color:#8A9BA8;font-size:12px;line-height:2">
    <div>목표 &nbsp;<strong style="color:#C8A84B">{goal}</strong></div>
    <div>시작 <strong style="color:#C8A84B">AD {start_year}년</strong> &nbsp;·&nbsp; 현재 <strong style="color:#C8A84B">AD {state.get('year',1)}년</strong></div>
    <div>총 턴 <strong style="color:#C8A84B">{turn}</strong> &nbsp;·&nbsp; 사망 <strong style="color:#C8A84B">{death_count}</strong>회</div>
  </div>
</header>

<!-- 레이아웃 -->
<div style="display:grid;grid-template-columns:260px 1fr;max-width:1140px;margin:0 auto">

  <!-- 사이드바 -->
  <aside style="border-right:1px solid #2A3448;padding:24px 20px;display:flex;flex-direction:column;gap:24px">

    <div>
      <div style="font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#7A6530;margin-bottom:10px">현재 신분</div>
      {''.join(f'<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #2A3448;font-size:13px"><span style="color:#8A9BA8">{k}</span><span style="font-weight:600;color:#EDE5CF">{v}</span></div>' for k, v in [("이름", name), ("신분", role), ("위치", location), ("겉나이", f"{apparent_age}세")])}
    </div>

    <div>
      <div style="font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#7A6530;margin-bottom:10px">세력 현황</div>
      <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #2A3448;font-size:13px">
        <span style="color:#8A9BA8">부족 영향력</span><span>{stars(influence)}</span>
      </div>
      <div style="display:flex;justify-content:space-between;padding:5px 0;font-size:13px">
        <span style="color:#8A9BA8">영향 인구</span><span style="font-weight:600">{population:,}명</span>
      </div>
    </div>

    <div>
      <div style="font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#7A6530;margin-bottom:10px">군사력</div>
      {build_military(state)}
    </div>

    <div>
      <div style="font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#7A6530;margin-bottom:10px">위협</div>
      {build_threats(state)}
    </div>

    <div>
      <div style="font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#7A6530;margin-bottom:10px">자산</div>
      {build_assets(state)}
    </div>

    <div>
      <div style="font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#7A6530;margin-bottom:10px">주요 인물</div>
      {build_relationships(state)}
    </div>

    <div>
      <div style="font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#7A6530;margin-bottom:6px">기술 도입 현황</div>
      <div style="font-size:11px;color:#4A5568;margin-bottom:8px">● 완료 &nbsp; ◐ 진행 &nbsp; ○ 가능 &nbsp; · 잠김</div>
      {build_tech_rows(techs)}
    </div>

  </aside>

  <!-- 메인 -->
  <main style="padding:28px 32px">
    {build_current_card(state)}

    <div style="font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:#7A6530;margin-bottom:16px;padding-bottom:6px;border-bottom:1px solid #2A3448">연대기 (최신순)</div>

    <div style="position:relative;padding-left:24px;border-left:1px solid #2A3448">
      {build_events(events)}
    </div>
  </main>

</div>
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
