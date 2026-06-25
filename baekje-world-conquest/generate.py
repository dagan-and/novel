#!/usr/bin/env python3
"""백제 전황 브리핑 HTML 생성기."""

import json
from html import escape
from pathlib import Path


BASE = Path(__file__).parent
SOURCE = BASE / "turns.json"
OUTPUT = BASE / "chronicle.html"


def load_turns(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def render_list(items, empty_message):
    if not items:
        return f'<p class="empty">{escape(empty_message)}</p>'
    return "".join(f"<li>{escape(item)}</li>" for item in items)


def render_paragraphs(items, empty_message):
    if not items:
        return f'<p class="empty">{escape(empty_message)}</p>'
    return "".join(f"<p>{escape(item)}</p>" for item in items)


def render_turn(turn):
    turn_number = turn["turn"]
    year = escape(turn["year"])
    codename = escape(turn["codename"])
    headline = escape(turn["headline"])
    outcome = escape(turn["outcome"])

    summary = render_paragraphs(turn.get("summary", []), "기록된 브리핑 없음")
    actions = render_list(turn.get("actions", []), "기록된 조치 없음")
    state_changes = render_list(turn.get("state_changes", []), "기록된 변화 없음")
    risks = render_list(turn.get("risks", []), "즉시 식별된 위험 없음")
    frontline = escape(turn.get("frontline", "전선 변화 없음"))
    court_reaction = escape(turn.get("court_reaction", "궁정 반응 기록 없음"))
    enemy_reaction = escape(turn.get("enemy_reaction", "적국 반응 기록 없음"))

    return f"""
    <section class="turn-card" data-turn="{turn_number}">
      <div class="eyebrow">TURN {turn_number:03d}</div>
      <div class="turn-header">
        <div>
          <h2>{year}</h2>
          <p class="codename">{codename}</p>
        </div>
        <div class="turn-badge">전황 브리핑</div>
      </div>
      <p class="headline">{headline}</p>
      <div class="summary-box">
        <div class="section-label">상황 개요</div>
        {summary}
      </div>
      <div class="grid">
        <article class="panel">
          <div class="section-label">주요 조치</div>
          <ul>{actions}</ul>
        </article>
        <article class="panel">
          <div class="section-label">작전 결과</div>
          <p>{outcome}</p>
        </article>
      </div>
      <div class="grid">
        <article class="panel accent">
          <div class="section-label">전선 동향</div>
          <p>{frontline}</p>
        </article>
        <article class="panel accent">
          <div class="section-label">궁정 반응</div>
          <p>{court_reaction}</p>
        </article>
      </div>
      <div class="grid">
        <article class="panel accent">
          <div class="section-label">적국 반응</div>
          <p>{enemy_reaction}</p>
        </article>
        <article class="panel">
          <div class="section-label">국가 변화</div>
          <ul>{state_changes}</ul>
        </article>
        <article class="panel warning">
          <div class="section-label">다음 턴 위험</div>
          <ul>{risks}</ul>
        </article>
      </div>
    </section>
    """


def generate_html(turns):
    cards = "".join(render_turn(turn) for turn in turns)
    total_turns = len(turns)
    start_turn = turns[0]["turn"] if turns else 0
    end_turn = turns[-1]["turn"] if turns else 0

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>백제 세계정복 전황 연대기</title>
<style>
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  min-height: 100vh;
  background:
    radial-gradient(circle at top, rgba(190, 60, 20, 0.18), transparent 35%),
    linear-gradient(180deg, #090c12 0%, #111622 45%, #090c12 100%);
  color: #f2e8d5;
  font-family: "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
}}
main {{
  width: min(960px, calc(100% - 32px));
  margin: 0 auto;
  padding: 32px 0 48px;
}}
.hero {{
  border: 1px solid rgba(220, 157, 85, 0.35);
  background: rgba(9, 14, 22, 0.78);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.35);
}}
.eyebrow {{
  font-size: 11px;
  letter-spacing: 0.28em;
  color: #d7a45d;
  text-transform: uppercase;
}}
h1 {{
  margin: 10px 0 8px;
  font-size: clamp(28px, 5vw, 46px);
  line-height: 1.05;
}}
.hero p {{
  margin: 0;
  color: #aeb8c9;
  line-height: 1.7;
}}
.meta {{
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 18px;
}}
.meta-chip {{
  border: 1px solid rgba(215, 164, 93, 0.24);
  background: rgba(215, 164, 93, 0.08);
  border-radius: 999px;
  padding: 8px 12px;
  color: #f2e8d5;
  font-size: 13px;
}}
.viewer {{
  margin-top: 22px;
  border-radius: 20px;
  overflow: hidden;
  border: 1px solid rgba(88, 106, 134, 0.35);
  background: rgba(13, 18, 28, 0.88);
}}
.toolbar {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 18px 20px;
  border-bottom: 1px solid rgba(88, 106, 134, 0.28);
}}
.toolbar-left {{
  display: flex;
  flex-direction: column;
  gap: 6px;
}}
.toolbar-right {{
  display: flex;
  gap: 10px;
}}
.turn-counter {{
  font-size: 13px;
  color: #d7a45d;
}}
.turn-name {{
  font-size: 20px;
  font-weight: 700;
}}
button {{
  border: 1px solid rgba(215, 164, 93, 0.3);
  background: rgba(215, 164, 93, 0.08);
  color: #f2e8d5;
  border-radius: 999px;
  padding: 10px 16px;
  font-size: 14px;
  cursor: pointer;
}}
button:disabled {{
  opacity: 0.4;
  cursor: default;
}}
.turn-stage {{
  padding: 20px;
}}
.turn-card {{
  display: none;
  animation: fadeIn 180ms ease;
}}
.turn-card.active {{
  display: block;
}}
.turn-header {{
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: end;
  margin-top: 8px;
}}
.turn-header h2 {{
  margin: 0;
  font-size: clamp(24px, 4vw, 36px);
}}
.codename {{
  margin: 6px 0 0;
  color: #d7a45d;
}}
.turn-badge {{
  border-left: 3px solid #c95839;
  padding-left: 12px;
  color: #f2e8d5;
  font-size: 13px;
}}
.headline {{
  margin: 22px 0 18px;
  font-size: clamp(22px, 3vw, 30px);
  line-height: 1.35;
  font-weight: 700;
}}
.summary-box,
.panel {{
  border: 1px solid rgba(88, 106, 134, 0.28);
  background: rgba(20, 28, 42, 0.92);
  border-radius: 18px;
  padding: 18px;
}}
.summary-box {{
  margin-bottom: 16px;
  border-left: 4px solid #c95839;
}}
.section-label {{
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #d7a45d;
  margin-bottom: 10px;
}}
.grid {{
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-top: 16px;
}}
.panel.warning {{
  border-left: 4px solid #d7a45d;
}}
.panel.accent {{
  border-left: 4px solid #6d88a7;
}}
ul {{
  margin: 0;
  padding-left: 18px;
}}
li, .panel p, .summary-box p {{
  line-height: 1.75;
  color: #eef3ff;
}}
.empty {{
  color: #90a0b7;
  margin: 0;
}}
@keyframes fadeIn {{
  from {{ opacity: 0; transform: translateY(8px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}
@media (max-width: 720px) {{
  main {{
    width: min(100% - 20px, 960px);
  }}
  .toolbar,
  .turn-header {{
    flex-direction: column;
    align-items: flex-start;
  }}
  .toolbar-right {{
    width: 100%;
  }}
  button {{
    flex: 1;
  }}
  .grid {{
    grid-template-columns: 1fr;
  }}
}}
</style>
</head>
<body>
<main>
  <section class="hero">
    <div class="eyebrow">BAEKJE WORLD CONQUEST</div>
    <h1>천인의 백제 세계정복 전황 연대기</h1>
    <p>짧은 턴 데이터를 바탕으로 생성된 한글 브리핑 화면이다. 초월적 기술혁명과 국가 운영 격차가 어떻게 전쟁의 양상을 바꾸는지 턴별로 확인할 수 있다.</p>
    <div class="meta">
      <div class="meta-chip">기록 범위: {start_turn:03d}턴 ~ {end_turn:03d}턴</div>
      <div class="meta-chip">총 기록 수: {total_turns}턴</div>
      <div class="meta-chip">형식: 드라마틱 전황 브리핑</div>
    </div>
  </section>

  <section class="viewer">
    <div class="toolbar">
      <div class="toolbar-left">
        <div id="turnCounter" class="turn-counter"></div>
        <div id="turnName" class="turn-name"></div>
      </div>
      <div class="toolbar-right">
        <button id="prevButton" type="button">이전 턴</button>
        <button id="nextButton" type="button">다음 턴</button>
      </div>
    </div>
    <div class="turn-stage">
      {cards}
    </div>
  </section>
</main>
<script>
const cards = Array.from(document.querySelectorAll(".turn-card"));
const turnCounter = document.getElementById("turnCounter");
const turnName = document.getElementById("turnName");
const prevButton = document.getElementById("prevButton");
const nextButton = document.getElementById("nextButton");
let activeIndex = 0;

function syncTurn(index) {{
  cards.forEach((card, cardIndex) => {{
    card.classList.toggle("active", cardIndex === index);
  }});

  const activeCard = cards[index];
  const turn = activeCard.dataset.turn.padStart(3, "0");
  const codename = activeCard.querySelector(".codename").textContent;

  turnCounter.textContent = `현재 표시: TURN ${{turn}} / 총 {total_turns}턴`;
  turnName.textContent = codename;
  prevButton.disabled = index === 0;
  nextButton.disabled = index === cards.length - 1;
}}

prevButton.addEventListener("click", () => {{
  if (activeIndex === 0) return;
  activeIndex -= 1;
  syncTurn(activeIndex);
}});

nextButton.addEventListener("click", () => {{
  if (activeIndex === cards.length - 1) return;
  activeIndex += 1;
  syncTurn(activeIndex);
}});

syncTurn(activeIndex);
</script>
</body>
</html>
"""


def write_html(turns, destination):
    destination.write_text(generate_html(turns), encoding="utf-8")


def main():
    turns = load_turns(SOURCE)
    write_html(turns, OUTPUT)
    print(f"[ok] {OUTPUT.name} generated")


if __name__ == "__main__":
    main()
