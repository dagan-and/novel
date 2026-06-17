#!/usr/bin/env python3
import os
import re
from pathlib import Path

from batch_paths import batch_bounds, html_episode_path, iter_episode_files

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SETTING_FILES = [
    {'src': 'setting/세계관.md', 'out': 'setting/세계관.html', 'title': '세계관'},
    {'src': 'setting/장기연재계획.md', 'out': 'setting/장기연재계획.html', 'title': '장기 연재 계획'},
]

# ── GENERIC DARK STYLE (세계관) ───────────────────────────────────────────────

DARK_STYLE = """
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #1a1a1a;
      color: #e8e0d0;
      font-family: 'Nanum Myeongjo', Georgia, serif;
      font-size: 1.21rem;
      line-height: 1.85;
      max-width: 960px;
      margin: 0 auto;
      padding: 3rem 1.5rem 5rem;
      word-break: keep-all;
    }
    h1 { font-size: 1.88rem; color: #c9a0b8; margin-bottom: 2rem; letter-spacing: 0.08em; }
    h2 { font-size: 1.31rem; color: #c9a0b8; margin: 2.2rem 0 0.7rem; padding-bottom: 0.3rem; border-bottom: 1px solid #2a2a2a; letter-spacing: 0.05em; }
    h3 { font-size: 1.19rem; color: #b08098; margin: 1.4rem 0 0.4rem; }
    p { margin: 0.5rem 0; }
    ul { padding-left: 1.4rem; margin: 0.4rem 0; }
    li { margin: 0.25rem 0; }
    hr { border: none; border-top: 1px solid #2a2a2a; margin: 1.8rem 0; }
    strong { color: #c8a8b8; }
    em { color: #a0a0a0; font-style: italic; }
    blockquote { border-left: 3px solid #3a2030; padding-left: 1rem; color: #a0a0a0; margin: 0.8rem 0; }
    .table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; margin: 1rem 0; }
    table { width: max-content; min-width: 100%; border-collapse: collapse; font-size: 1.13rem; }
    th { background: #222; color: #c9a0b8; padding: 0.5rem 0.75rem; text-align: left; border-bottom: 1px solid #3a2030; white-space: nowrap; }
    td { padding: 0.45rem 0.75rem; border-bottom: 1px solid #252525; vertical-align: top; }
    tr:hover td { background: #1f1f1f; }
    code { background: #222; color: #c9a0b8; padding: 0.1rem 0.35rem; border-radius: 2px; font-size: 1.1rem; }
    .back { display: inline-block; margin-bottom: 2rem; color: #c9a0b8; text-decoration: none; font-size: 1.1rem; }
    .back:hover { text-decoration: underline; }
"""

# ── GAME CSS BASE (관계망, 연대기 공통) ───────────────────────────────────────

GAME_CSS_BASE = """
    :root {
      --bg:#08061a; --panel:#110f28; --panel2:#1a1840;
      --border:#2a2260; --border-hi:#5040a0;
      --pink:#c050a8; --purple:#7040d0; --blue:#4080d0; --cyan:#40b0c0;
      --green:#30a860; --orange:#c07828; --red:#c03040;
      --text:#e0d8f8; --text2:#9080b8; --text3:#5040a0;
      --c-sian:#9060d0; --c-soyu:#c050a8; --c-haeun:#4090c0;
      --c-seojin:#50b090; --c-daon:#c0a030;
    }
    * { box-sizing:border-box; margin:0; padding:0; }
    body {
      background:var(--bg); color:var(--text);
      font-family:'Noto Sans KR',-apple-system,'Helvetica Neue',sans-serif;
      min-height:100vh; padding:2rem 1.5rem 5rem;
      max-width:1080px; margin:0 auto;
    }
    .nav-bar { display:flex; gap:0.5rem; margin-bottom:1.5rem; }
    .nav-bar a {
      padding:0.3rem 0.9rem; border-radius:4px; font-size:0.75rem;
      text-decoration:none; border:1px solid var(--border); color:var(--text2);
      transition:all 0.2s;
    }
    .nav-bar a:hover { border-color:var(--border-hi); color:var(--text); }
    .nav-bar a.active { border-color:var(--pink); color:var(--pink); background:rgba(192,80,168,0.1); }
    .section-title {
      display:flex; align-items:center; gap:0.75rem;
      margin:2.2rem 0 1rem; color:var(--text2);
      font-size:0.72rem; letter-spacing:0.14em; text-transform:uppercase;
    }
    .section-title::before,.section-title::after { content:''; flex:1; height:1px; background:var(--border); }
"""

KANGEMANG_CSS = GAME_CSS_BASE + """
    .game-header {
      display:flex; align-items:center; gap:1.5rem;
      padding:1.5rem 1.75rem; background:var(--panel);
      border:1px solid var(--border); border-radius:10px; margin-bottom:2rem;
      position:relative; overflow:hidden;
    }
    .game-header::before {
      content:''; position:absolute; top:0;left:0;right:0;bottom:0;
      background:linear-gradient(135deg,rgba(112,64,208,0.15) 0%,transparent 55%);
      pointer-events:none;
    }
    .player-avatar {
      width:68px; height:68px; border-radius:50%;
      background:linear-gradient(135deg,var(--purple),var(--pink));
      display:flex; align-items:center; justify-content:center;
      font-size:1.5rem; font-weight:700; color:white;
      box-shadow:0 0 20px rgba(192,80,168,0.35); flex-shrink:0;
      border:2px solid rgba(192,80,168,0.4);
    }
    .player-info h1 { font-size:1.5rem; font-weight:700; color:var(--text); letter-spacing:0.06em; margin-bottom:0.5rem; }
    .player-tags { display:flex; gap:0.4rem; flex-wrap:wrap; }
    .tag { padding:0.2rem 0.65rem; border-radius:20px; font-size:0.72rem; border:1px solid; letter-spacing:0.03em; }
    .tag-loop { border-color:var(--cyan); color:var(--cyan); background:rgba(64,176,192,0.08); }
    .tag-year { border-color:var(--purple); color:#a080e8; background:rgba(112,64,208,0.08); }
    .tag-loc  { border-color:var(--text3); color:var(--text2); background:rgba(80,64,160,0.08); }
    .harem-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(230px,1fr)); gap:0.9rem; }
    .char-card {
      background:var(--panel); border:1px solid var(--border); border-radius:10px; padding:1.2rem;
      position:relative; overflow:hidden;
      transition:border-color 0.2s,transform 0.15s,box-shadow 0.2s;
    }
    .char-card:hover { border-color:var(--border-hi); transform:translateY(-2px); box-shadow:0 8px 24px rgba(0,0,0,0.4); }
    .char-card.main { border-top:2px solid var(--pink); }
    .char-card.sub  { border-top:2px solid var(--blue); }
    .char-card::before { content:''; position:absolute; top:0; right:0; width:100px; height:100px; border-radius:50%; pointer-events:none; opacity:0.06; }
    .char-card.main::before { background:radial-gradient(var(--pink),transparent); }
    .char-card.sub::before  { background:radial-gradient(var(--blue),transparent); }
    .char-card-header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.9rem; }
    .char-avatar { width:46px; height:46px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:0.82rem; font-weight:700; color:white; flex-shrink:0; }
    .char-avatar.main { background:linear-gradient(135deg,#802080,#c050a8); box-shadow:0 0 10px rgba(192,80,168,0.3); }
    .char-avatar.sub  { background:linear-gradient(135deg,#204080,#4080d0); box-shadow:0 0 10px rgba(64,128,208,0.3); }
    .char-badge { padding:0.18rem 0.55rem; border-radius:3px; font-size:0.65rem; font-weight:700; letter-spacing:0.04em; }
    .badge-main { background:linear-gradient(135deg,#a030a0,#c050a8); color:white; }
    .badge-sub  { background:linear-gradient(135deg,#204880,#4080c0); color:white; }
    .char-name { font-size:1.05rem; font-weight:700; color:var(--text); margin-bottom:0.8rem; }
    .stat-row { margin-bottom:0.55rem; }
    .stat-label { display:flex; justify-content:space-between; font-size:0.67rem; color:var(--text3); letter-spacing:0.05em; margin-bottom:0.25rem; }
    .stat-label span { color:var(--text2); font-weight:500; }
    .stat-bar { height:5px; background:rgba(45,36,96,0.8); border-radius:3px; overflow:hidden; }
    .stat-bar-fill { height:100%; border-radius:3px; }
    .fill-main { background:linear-gradient(90deg,#7030c0,#c050a8); }
    .fill-sub  { background:linear-gradient(90deg,#2050a0,#4080d0); }
    .stage-label { display:flex; justify-content:space-between; font-size:0.67rem; color:var(--text3); letter-spacing:0.05em; margin-bottom:0.3rem; }
    .stage-label span { color:var(--text2); font-weight:500; }
    .stage-orbs { display:flex; gap:0.35rem; }
    .orb { width:9px; height:9px; border-radius:50%; background:rgba(45,36,96,0.8); border:1px solid var(--border-hi); }
    .orb.filled-main { background:var(--pink); box-shadow:0 0 6px rgba(192,80,168,0.6); border-color:var(--pink); }
    .orb.filled-sub  { background:var(--blue); box-shadow:0 0 6px rgba(64,128,208,0.6); border-color:var(--blue); }
    .char-status { margin-top:0.8rem; font-size:0.75rem; color:var(--text2); line-height:1.55; padding-top:0.75rem; border-top:1px solid var(--border); }
    .rel-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); gap:0.8rem; }
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
    .rel-card { background:var(--panel); border:1px solid var(--border); border-left-width:3px; border-radius:8px; padding:1rem 1.2rem; transition:border-color 0.2s; }
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
    .type-legend { display:flex; gap:0.9rem; flex-wrap:wrap; margin-top:0.9rem; }
    .legend-entry { display:flex; align-items:center; gap:0.3rem; font-size:0.65rem; color:var(--text3); }
    .legend-bar { width:3px; height:12px; border-radius:2px; }
    .rel-pair-header { display:flex; align-items:center; gap:0.5rem; margin-bottom:0.7rem; }
    .rel-avatar-sm { width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:0.6rem; font-weight:700; color:white; flex-shrink:0; }
    .rel-vs { font-size:0.65rem; color:var(--text3); }
    .rel-pair-name { font-size:0.85rem; font-weight:600; color:var(--text); }
    .rel-section { margin-bottom:0.45rem; }
    .rel-section-label { font-size:0.62rem; color:var(--text3); letter-spacing:0.06em; text-transform:uppercase; margin-bottom:0.2rem; }
    .rel-section-text { font-size:0.75rem; color:var(--text2); line-height:1.55; }
    .rel-honorifics { display:flex; gap:0.4rem; margin-top:0.5rem; flex-wrap:wrap; }
    .honorific { font-size:0.68rem; padding:0.12rem 0.5rem; background:rgba(42,34,96,0.6); border:1px solid var(--border); border-radius:3px; color:var(--text2); }
    .honorific b { color:var(--text); }
    .quest-list { display:grid; gap:0.55rem; }
    .quest-item { display:grid; grid-template-columns:32px 1fr auto; gap:0.8rem; align-items:start; background:var(--panel); border:1px solid var(--border); border-radius:6px; padding:0.7rem 1rem; transition:border-color 0.2s; }
    .quest-item:hover { border-color:var(--border-hi); }
    .quest-icon { width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:0.75rem; flex-shrink:0; margin-top:1px; }
    .qi-done   { background:rgba(40,160,80,0.15);  border:1px solid rgba(48,168,96,0.5); }
    .qi-active { background:rgba(192,120,40,0.15); border:1px solid rgba(192,120,40,0.5); }
    .quest-text { font-size:0.78rem; color:var(--text); line-height:1.5; margin-bottom:0.25rem; }
    .quest-ep { font-size:0.67rem; color:var(--text3); }
    .quest-ep span { color:var(--text2); }
    .qs-badge { font-size:0.67rem; padding:0.15rem 0.5rem; border-radius:3px; white-space:nowrap; align-self:start; font-weight:500; }
    .qs-done   { background:rgba(40,160,80,0.12); color:#40c060; border:1px solid rgba(48,168,96,0.3); }
    .qs-active { background:rgba(192,120,40,0.12); color:#e09040; border:1px solid rgba(200,120,40,0.3); }
"""

YONDAEGI_CSS = GAME_CSS_BASE + """
    .page-header { padding:1.5rem 1.75rem; background:var(--panel); border:1px solid var(--border); border-radius:10px; margin-bottom:2rem; position:relative; overflow:hidden; }
    .page-header::before { content:''; position:absolute; top:0;left:0;right:0;bottom:0; background:linear-gradient(135deg,rgba(64,176,192,0.1) 0%,transparent 55%); pointer-events:none; }
    .page-header h1 { font-size:1.3rem; font-weight:700; color:var(--text); letter-spacing:0.05em; margin-bottom:0.4rem; }
    .page-header p { font-size:0.8rem; color:var(--text2); }
    .char-legend { display:flex; gap:0.5rem; flex-wrap:wrap; margin-bottom:1.5rem; }
    .legend-item { display:flex; align-items:center; gap:0.35rem; padding:0.2rem 0.6rem; background:var(--panel); border:1px solid var(--border); border-radius:20px; font-size:0.7rem; color:var(--text2); }
    .legend-dot { width:8px; height:8px; border-radius:50%; }
    .arc-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:0.8rem; margin-bottom:1rem; }
    .arc-card { background:var(--panel); border:1px solid var(--border); border-left:3px solid var(--purple); border-radius:8px; padding:1rem 1.1rem; }
    .arc-range { font-size:0.65rem; color:var(--cyan); letter-spacing:0.06em; margin-bottom:0.4rem; font-weight:600; }
    .arc-event { font-size:0.78rem; color:var(--text); line-height:1.5; margin-bottom:0.5rem; }
    .arc-rel { font-size:0.7rem; color:var(--text2); line-height:1.45; padding-top:0.5rem; border-top:1px solid var(--border); }
    .ep-grid { display:grid; gap:0.65rem; }
    .ep-card { display:grid; grid-template-columns:72px 1fr; background:var(--panel); border:1px solid var(--border); border-radius:8px; overflow:hidden; transition:border-color 0.2s,box-shadow 0.2s; }
    .ep-card:hover { border-color:var(--border-hi); box-shadow:0 4px 16px rgba(0,0,0,0.35); }
    .ep-card.has-adult { border-left:3px solid var(--pink); }
    .ep-card.has-event { border-left:3px solid var(--cyan); }
    .ep-card.has-crisis { border-left:3px solid var(--red); }
    .ep-num-col { background:var(--panel2); display:flex; flex-direction:column; align-items:center; justify-content:center; padding:0.8rem 0.4rem; border-right:1px solid var(--border); flex-shrink:0; }
    .ep-num { font-size:1.1rem; font-weight:700; color:var(--text); line-height:1; }
    .ep-num-label { font-size:0.55rem; color:var(--text3); letter-spacing:0.08em; text-transform:uppercase; margin-top:0.2rem; }
    .ep-body { padding:0.8rem 1rem; }
    .ep-meta { display:flex; gap:0.4rem; flex-wrap:wrap; margin-bottom:0.5rem; align-items:center; }
    .ep-date { font-size:0.67rem; color:var(--text3); }
    .ep-loc { font-size:0.67rem; color:var(--text2); }
    .ep-loc::before { content:'📍 '; }
    .ep-summary { font-size:0.8rem; color:var(--text); line-height:1.55; margin-bottom:0.5rem; }
    .ep-footer { display:flex; gap:0.35rem; flex-wrap:wrap; align-items:center; }
    .char-chip { padding:0.12rem 0.45rem; border-radius:20px; font-size:0.62rem; font-weight:500; border:1px solid; }
    .cc-sian   { border-color:var(--c-sian);   color:var(--c-sian);   background:rgba(144,96,208,0.1); }
    .cc-soyu   { border-color:var(--c-soyu);   color:var(--c-soyu);   background:rgba(192,80,168,0.1); }
    .cc-haeun  { border-color:var(--c-haeun);  color:var(--c-haeun);  background:rgba(64,144,192,0.1); }
    .cc-seojin { border-color:var(--c-seojin); color:var(--c-seojin); background:rgba(80,176,144,0.1); }
    .cc-daon   { border-color:var(--c-daon);   color:var(--c-daon);   background:rgba(192,160,48,0.1); }
    .badge { padding:0.12rem 0.45rem; border-radius:3px; font-size:0.62rem; font-weight:600; }
    .b-adult  { background:rgba(192,80,168,0.15); color:#e060c0; border:1px solid rgba(192,80,168,0.3); }
    .b-turn   { background:rgba(64,176,192,0.12); color:#40c0d8; border:1px solid rgba(64,176,192,0.3); }
    .b-mild   { background:rgba(112,64,208,0.12); color:#9060e0; border:1px solid rgba(112,64,208,0.3); }
    .b-crisis { background:rgba(192,48,64,0.15);  color:#e04060; border:1px solid rgba(192,48,64,0.3); }
"""

# ── PARSING UTILITIES ─────────────────────────────────────────────────────────

def inline_md(text):
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    return text


def md_to_html(text):
    lines = text.split('\n')
    out = []
    in_table = False
    table_head = True
    in_ul = False

    for line in lines:
        if line.startswith('|'):
            if not in_table:
                out.append('<div class="table-wrap"><table>')
                in_table = True
                table_head = True
            if re.match(r'^\|[-| ]+\|$', re.sub(r'\s', '', line)):
                out.append('<tbody>')
                table_head = False
                continue
            tag = 'th' if table_head else 'td'
            cells = line.strip('|').split('|')
            cells_html = ''.join(f'<{tag}>{inline_md(c.strip())}</{tag}>' for c in cells)
            out.append(f'<tr>{cells_html}</tr>')
            continue
        elif in_table:
            out.append('</tbody></table></div>')
            in_table = False
            table_head = True

        if re.match(r'^- ', line):
            if not in_ul:
                out.append('<ul>')
                in_ul = True
            out.append(f'<li>{inline_md(line[2:])}</li>')
            continue
        elif in_ul:
            out.append('</ul>')
            in_ul = False

        if re.match(r'^### ', line):
            out.append(f'<h3>{inline_md(line[4:])}</h3>')
        elif re.match(r'^## ', line):
            out.append(f'<h2>{inline_md(line[3:])}</h2>')
        elif re.match(r'^# ', line):
            out.append(f'<h1>{inline_md(line[2:])}</h1>')
        elif re.match(r'^-{3,}$', line.strip()):
            out.append('<hr>')
        elif re.match(r'^> ', line):
            out.append(f'<blockquote>{inline_md(line[2:])}</blockquote>')
        elif not line.strip():
            out.append('')
        else:
            out.append(f'<p>{inline_md(line)}</p>')

    if in_table:
        out.append('</tbody></table></div>')
    if in_ul:
        out.append('</ul>')
    return '\n'.join(out)


def get_h2_section(text, heading):
    """## heading 이후부터 다음 ## 또는 끝까지 추출."""
    pattern = rf'(?:^|\n)## {re.escape(heading)}\n([\s\S]*?)(?=\n## |\Z)'
    m = re.search(pattern, text)
    return m.group(1).strip() if m else ''


def parse_bullets_to_dict(text):
    """'- key: value' 형식 → dict."""
    result = {}
    for line in text.split('\n'):
        m = re.match(r'^-\s+(.+?):\s+(.+)', line.strip())
        if m:
            result[m.group(1).strip()] = m.group(2).strip()
    return result


def parse_md_tables(text):
    """텍스트에서 모든 마크다운 테이블 파싱 → [{headers, rows}, ...]."""
    results = []
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith('|'):
            tlines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                tlines.append(lines[i])
                i += 1
            headers = []
            rows = []
            for line in tlines:
                cells = [c.strip() for c in line.strip('|').split('|')]
                if all(re.match(r'^[-: ]+$', c) for c in cells if c):
                    continue
                if not headers:
                    headers = cells
                else:
                    rows.append(dict(zip(headers, cells)))
            if headers and rows:
                results.append({'headers': headers, 'rows': rows})
        else:
            i += 1
    return results


def get_h3_subsections(text):
    """### 로 분리 → [(title, body), ...]."""
    parts = re.split(r'\n### ', '\n' + text)
    result = []
    for part in parts:
        if not part.strip():
            continue
        lines = part.strip().split('\n', 1)
        title = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ''
        if title:
            result.append((title, body))
    return result


# ── CHARACTER HELPERS ─────────────────────────────────────────────────────────

CHAR_COLOR_MAIN = 'linear-gradient(135deg,#802080,#c050a8)'
CHAR_COLOR_SUB  = 'linear-gradient(135deg,#204080,#4080d0)'

CHAR_CSS_CLASS = {
    '김시안': 'cc-sian', '임소율': 'cc-soyu', '이하은': 'cc-haeun',
    '한서진': 'cc-seojin', '정다온': 'cc-daon',
}

INTIMACY_WIDTH = {'깊은': 100, '보통': 55, '얕은': 30, '없음': 10}

EVENT_BADGE = {
    '관계 전환': '<span class="badge b-turn">관계 전환</span>',
    '약한 변화':  '<span class="badge b-mild">변화</span>',
    '중대한 위기': '<span class="badge b-crisis">위기</span>',
}


def given_name(full_name):
    """임소율 → 소율."""
    return full_name[1:] if len(full_name) >= 3 else full_name


# ── RENDERER: 관계망 ──────────────────────────────────────────────────────────

def render_kangemang(md_text):
    player = parse_bullets_to_dict(get_h2_section(md_text, '김시안 현재 상태'))
    harem_tables = parse_md_tables(get_h2_section(md_text, '하렘 현황'))
    harem_rows = harem_tables[0]['rows'] if harem_tables else []
    rel_subsections = get_h3_subsections(get_h2_section(md_text, '멤버 간 관계망'))
    quest_tables = parse_md_tables(get_h2_section(md_text, '복선 트래커'))
    quest_rows = quest_tables[0]['rows'] if quest_tables else []

    char_type_map = {r.get('이름', ''): r.get('구분', '') for r in harem_rows}

    # ── 플레이어 헤더
    header_html = f'''
  <div class="game-header">
    <div class="player-avatar">시안</div>
    <div class="player-info">
      <h1>김시안</h1>
      <div class="player-tags">
        <span class="tag tag-loop">{player.get('루프', '')}</span>
        <span class="tag tag-year">{player.get('연도', '')}</span>
        <span class="tag tag-loc">{player.get('나이', '')} · {player.get('거주지', '')}</span>
      </div>
    </div>
  </div>'''

    # ── 하렘 카드
    cards = []
    for row in harem_rows:
        name     = row.get('이름', '')
        type_    = row.get('구분', '')
        intimacy = row.get('친밀도', '')
        stage_s  = row.get('관계 진도', '')
        status = re.sub(r'^활성\s*[—\-]\s*', '', row.get('현재 상태', ''))
        status = re.sub(r'[\.\s]*호감도\s*\d+/\d+', '', status).strip()

        tc = 'main' if type_ == '메인' else 'sub'
        bc = 'badge-main' if type_ == '메인' else 'badge-sub'
        fc = 'fill-main'  if type_ == '메인' else 'fill-sub'
        w  = INTIMACY_WIDTH.get(intimacy, 50)

        cards.append(f'''
    <div class="char-card {tc}">
      <div class="char-card-header">
        <div class="char-avatar {tc}">{given_name(name)}</div>
        <span class="char-badge {bc}">{type_}</span>
      </div>
      <div class="char-name">{name}</div>
      <div class="stat-row">
        <div class="stat-label">친밀도 <span>{intimacy}</span></div>
        <div class="stat-bar"><div class="stat-bar-fill {fc}" style="width:{w}%"></div></div>
      </div>
      <div class="char-status">{status}</div>
    </div>''')
    harem_html = f'<div class="harem-grid">{"".join(cards)}\n  </div>'

    # ── 멤버 간 관계망 — 타입 집계 + 인물 목록
    types_order = ['동맹', '긴장', '탐색', '우정']
    type_counts = {t: 0 for t in types_order}
    all_chars_ordered = []

    rel_cards = []
    for title, body in rel_subsections:
        nm = re.match(r'(.+?)\s*[×x]\s*(.+)', title)
        if not nm:
            continue
        n1, n2 = nm.group(1).strip(), nm.group(2).strip()
        c1 = CHAR_COLOR_MAIN if char_type_map.get(n1) == '메인' else CHAR_COLOR_SUB
        c2 = CHAR_COLOR_MAIN if char_type_map.get(n2) == '메인' else CHAR_COLOR_SUB

        bul = parse_bullets_to_dict(body)
        rel_type = bul.get('타입', '')
        current  = bul.get('현재', '')
        recent   = bul.get('최근 변화', '')
        hon_line = bul.get('호칭', '')
        pairs = re.findall(r'(\S+)\s*→\s*\S+\s*`([^`]+)`', hon_line)
        hons = ''.join(f'<div class="honorific"><b>{c}</b> → {h}</div>' for c, h in pairs)

        if rel_type in type_counts:
            type_counts[rel_type] += 1
        for name in [n1, n2]:
            gn = given_name(name)
            if gn not in all_chars_ordered:
                all_chars_ordered.append(gn)

        chars_attr = f'{given_name(n1)},{given_name(n2)}'
        rel_cards.append(f'''
    <div class="rel-card" data-type="{rel_type}" data-chars="{chars_attr}">
      <div class="rel-pair-header">
        <div style="display:flex;align-items:center;gap:0.5rem;flex:1;min-width:0">
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

    # 필터 UI
    total = sum(type_counts.values())
    type_tabs = f'<button class="type-tab active" data-type="all" onclick="filterRel(this,\'all\')">전체 ({total})</button>'
    for t in types_order:
        if type_counts[t]:
            type_tabs += f'<button class="type-tab" data-type="{t}" onclick="filterRel(this,\'{t}\')">{t} ({type_counts[t]})</button>'

    char_chips = '<span class="chip-label">인물</span>'
    char_chips += '<button class="char-chip-btn active" data-char="all" onclick="filterChar(this,\'all\')">전체</button>'
    for ch in all_chars_ordered:
        char_chips += f'<button class="char-chip-btn" data-char="{ch}" onclick="filterChar(this,\'{ch}\')">{ch}</button>'

    filter_js = '''<script>
var _rtype="all",_char="all";
function filterRel(btn,t){
  _rtype=t;
  document.querySelectorAll(".type-tab").forEach(function(b){b.classList.toggle("active",b.dataset.type===t);});
  applyRelFilter();
}
function filterChar(btn,c){
  _char=c;
  document.querySelectorAll(".char-chip-btn").forEach(function(b){b.classList.toggle("active",b.dataset.char===c);});
  applyRelFilter();
}
function applyRelFilter(){
  document.querySelectorAll(".rel-card").forEach(function(card){
    var tm=_rtype==="all"||card.dataset.type===_rtype;
    var cm=_char==="all"||card.dataset.chars.split(",").indexOf(_char)!==-1;
    card.classList.toggle("hidden",!(tm&&cm));
  });
}
</script>'''

    legend_html = '''  <div class="type-legend">
    <div class="legend-entry"><div class="legend-bar" style="background:#30a860"></div>동맹</div>
    <div class="legend-entry"><div class="legend-bar" style="background:#c07828"></div>긴장</div>
    <div class="legend-entry"><div class="legend-bar" style="background:#4080d0"></div>탐색</div>
    <div class="legend-entry"><div class="legend-bar" style="background:#40b0c0"></div>우정</div>
  </div>'''

    rel_html = f'''  <div class="filter-bar">
    <div class="type-tabs">{type_tabs}</div>
    <div class="char-chips">{char_chips}</div>
  </div>
  <div class="rel-grid">{"".join(rel_cards)}
  </div>
{legend_html}
{filter_js}'''

    # ── 복선 트래커
    quests = []
    for row in quest_rows:
        content = row.get('복선 내용', '')
        planted = row.get('심은 화수', '')
        expected = row.get('예정 회수', '')
        sm = re.match(r'^(진행|완료)\s*[—\-]\s*(.*)', row.get('상태', ''))
        stype = sm.group(1) if sm else '진행'
        sdesc = sm.group(2) if sm else ''
        if stype == '완료':
            ic, ic_sym, bc = 'qi-done', '✓', 'qs-done'
        else:
            ic, ic_sym, bc = 'qi-active', '▶', 'qs-active'
        ep_text = f'심은 화수 <span>{planted}</span> · 예정 회수 <span>{expected}</span>'
        if sdesc:
            ep_text += f' · {sdesc}'
        quests.append(f'''
    <div class="quest-item">
      <div class="quest-icon {ic}">{ic_sym}</div>
      <div>
        <div class="quest-text">{content}</div>
        <div class="quest-ep">{ep_text}</div>
      </div>
      <div class="qs-badge {bc}">{stype}</div>
    </div>''')
    quest_html = f'<div class="quest-list">{"".join(quests)}\n  </div>'

    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>관계망</title>
  <style>{KANGEMANG_CSS}</style>
</head>
<body>
  <div class="nav-bar">
    <a href="관계망.html" class="active">관계망</a>
    <a href="연대기.html">연대기</a>
    <a href="../index.html">← 메인</a>
  </div>
  {header_html}
  <div class="section-title"><span>◈</span> 하렘 현황</div>
  {harem_html}
  <div class="section-title"><span>◈</span> 멤버 간 관계망</div>
  {rel_html}
  <div class="section-title"><span>◈</span> 복선 트래커</div>
  {quest_html}
</body>
</html>'''


# ── RENDERER: 연대기 ──────────────────────────────────────────────────────────

def render_yondaegi(md_text):
    tables = parse_md_tables(md_text)
    arc_rows, ep_rows = [], []
    for t in tables:
        h = t['headers']
        if h and h[0] == '화수':
            arc_rows = t['rows']
        elif h and h[0].strip() == 'ep':
            ep_rows = t['rows']

    # ── 아크 카드
    arc_cards = []
    for row in arc_rows:
        arc_cards.append(f'''
    <div class="arc-card">
      <div class="arc-range">{row.get('화수','')}</div>
      <div class="arc-event">{row.get('핵심 사건','')}</div>
      <div class="arc-rel">{row.get('관계 변화','')}</div>
    </div>''')
    arc_html = f'<div class="arc-grid">{"".join(arc_cards)}\n  </div>'

    # ── 에피소드 카드
    ep_cards = []
    for row in ep_rows:
        ep_num   = row.get('ep', '').strip()
        date     = row.get('연도/계절', '').strip()
        loc      = row.get('장소', '').strip()
        chars_s  = row.get('등장', '').strip()
        summary  = row.get('한줄 요약', '').strip()
        adult    = row.get('성인씬', '').strip()
        event    = row.get('돌발 이벤트', '').strip()

        chips = ''.join(
            f'<span class="char-chip {CHAR_CSS_CLASS[c.strip()]}">{c.strip()}</span>'
            for c in chars_s.split(',') if c.strip() in CHAR_CSS_CLASS
        )
        badges = ''
        if adult == 'O':
            badges += '<span class="badge b-adult">성인씬</span>'
        if event and event != '-':
            badges += EVENT_BADGE.get(event, '')

        cls = ['ep-card']
        if adult == 'O':
            cls.append('has-adult')
        if event == '중대한 위기':
            cls.append('has-crisis')
        elif event in ('관계 전환', '약한 변화'):
            cls.append('has-event')

        ep_cards.append(f'''
    <div class="{' '.join(cls)}">
      <div class="ep-num-col">
        <div class="ep-num">{ep_num}</div>
        <div class="ep-num-label">EP</div>
      </div>
      <div class="ep-body">
        <div class="ep-meta">
          <span class="ep-date">{date}</span>
          <span class="ep-loc">{loc}</span>
        </div>
        <div class="ep-summary">{summary}</div>
        <div class="ep-footer">{chips}{badges}</div>
      </div>
    </div>''')
    ep_html = f'<div class="ep-grid">{"".join(ep_cards)}\n  </div>'

    legend = '''
  <div class="char-legend">
    <div class="legend-item"><div class="legend-dot" style="background:var(--c-sian)"></div>김시안</div>
    <div class="legend-item"><div class="legend-dot" style="background:var(--c-soyu)"></div>임소율</div>
    <div class="legend-item"><div class="legend-dot" style="background:var(--c-haeun)"></div>이하은</div>
    <div class="legend-item"><div class="legend-dot" style="background:var(--c-seojin)"></div>한서진</div>
    <div class="legend-item"><div class="legend-dot" style="background:var(--c-daon)"></div>정다온</div>
    <div style="flex:1"></div>
    <div class="legend-item" style="border-color:rgba(192,80,168,0.4)"><span style="color:var(--pink);font-weight:700">성</span>&nbsp;성인씬</div>
    <div class="legend-item" style="border-color:rgba(64,176,192,0.4)"><span style="color:var(--cyan);font-weight:700">전</span>&nbsp;관계 전환</div>
    <div class="legend-item" style="border-color:rgba(112,64,208,0.4)"><span style="color:#9060e0;font-weight:700">변</span>&nbsp;약한 변화</div>
    <div class="legend-item" style="border-color:rgba(192,48,64,0.4)"><span style="color:var(--red);font-weight:700">위</span>&nbsp;중대한 위기</div>
  </div>'''

    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>연대기</title>
  <style>{YONDAEGI_CSS}</style>
</head>
<body>
  <div class="nav-bar">
    <a href="관계망.html">관계망</a>
    <a href="연대기.html" class="active">연대기</a>
    <a href="../index.html">← 메인</a>
  </div>
  <div class="page-header">
    <h1>에피소드 연대기</h1>
    <p>1차 루프 · 2013~2014</p>
  </div>
  {legend}
  <div class="section-title"><span>◈</span> 스토리 아크 요약</div>
  {arc_html}
  <div class="section-title"><span>◈</span> 에피소드 상세</div>
  {ep_html}
</body>
</html>'''


# ── GENERIC BUILDER (세계관 등) ───────────────────────────────────────────────

def build_setting(src, out, title):
    src_path = os.path.join(BASE_DIR, src)
    if not os.path.exists(src_path):
        print(f'건너뜀: {src} 없음')
        return
    with open(src_path, encoding='utf-8') as f:
        raw = f.read()
    raw = re.sub(r'^# 다시 만나는 관계들\s*\n(?:\s*\n)?---\s*\n', '', raw, count=1)
    body = md_to_html(raw)
    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>{DARK_STYLE}</style>
</head>
<body>
  <a class="back" href="../index.html">← 메인</a>
  {body}
</body>
</html>'''
    out_path = os.path.join(BASE_DIR, 'html', out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'✓ html/{out} 생성 완료')


def build_game_page(src, out, renderer):
    src_path = os.path.join(BASE_DIR, src)
    if not os.path.exists(src_path):
        print(f'건너뜀: {src} 없음')
        return
    with open(src_path, encoding='utf-8') as f:
        raw = f.read()
    html = renderer(raw)
    out_path = os.path.join(BASE_DIR, 'html', out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'✓ html/{out} 생성 완료')


def build_index():
    html_dir = os.path.join(BASE_DIR, 'html')
    episodes_root = Path(BASE_DIR) / 'episodes'
    episode_paths = iter_episode_files(episodes_root, 'md')

    sections = []
    current_batch = None
    current_rows = []
    for row_start in range(0, len(episode_paths), 10):
        group = episode_paths[row_start:row_start + 10]
        if not group:
            continue
        start_num = int(re.search(r'\d+', group[0].stem).group())
        end_num = int(re.search(r'\d+', group[-1].stem).group())
        batch_range = batch_bounds(start_num)
        if batch_range != current_batch:
            if current_rows:
                sections.append((current_batch, ''.join(current_rows)))
                current_rows = []
            current_batch = batch_range
        links = ''.join(
            '<a href="{}">{}</a>'.format(
                os.path.relpath(html_episode_path(Path(BASE_DIR), path.stem), html_dir).replace(os.sep, '/'),
                int(re.search(r'\d+', path.stem).group()),
            )
            for path in group
        )
        current_rows.append(f'<div class="ep-group"><div class="ep-label">{start_num}~{end_num}화</div><div class="ep-links">{links}</div></div>')
    if current_rows:
        sections.append((current_batch, ''.join(current_rows)))

    ep_groups = ''.join(
        f'<div class="ep-batch"><h3>{start}~{end}화</h3>{rows}</div>'
        for (start, end), rows in sections
    )

    index_cards = [
        {'out': 'characters.html',           'title': '인물'},
        {'out': 'preludes.html',             'title': '삽화'},
        {'out': 'setting/장기연재계획.html', 'title': '장기 계획'},
    ]
    card_chunks = [
        '<a class="utility-button" href="{out}">{title}</a>'.format(**card)
        for card in index_cards
    ]
    setting_links = '\n      '.join(card_chunks)

    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>목차</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #1a1a1a;
      color: #e8e0d0;
      font-family: 'Nanum Myeongjo', Georgia, serif;
      max-width: 900px;
      margin: 0 auto;
      padding: 3rem 1.5rem 5rem;
    }}
    .subtitle {{ text-align: center; color: #666; font-size: 1.06rem; margin-bottom: 2rem; }}
    .index-layout {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 180px;
      gap: 1.5rem;
    }}
    .episode-sections {{
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }}
    .ep-batch {{
      background: #161616;
      border: 1px solid #2b2429;
      border-radius: 6px;
      padding: 1rem 1.1rem 1.2rem;
    }}
    .ep-batch h3 {{
      color: #c9a0b8;
      font-size: 1rem;
      letter-spacing: 0.08em;
      margin-bottom: 0.9rem;
    }}
    .ep-group {{
      display: grid;
      grid-template-columns: 88px minmax(0, 1fr);
      gap: 0.9rem;
      align-items: start;
      padding: 0.45rem 0;
      border-top: 1px solid #221d20;
    }}
    .ep-group:first-of-type {{ border-top: 0; padding-top: 0; }}
    .ep-label {{
      color: #8f7c88;
      font-size: 0.92rem;
      letter-spacing: 0.04em;
      padding-top: 0.15rem;
    }}
    .ep-links {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }}
    .ep-links a {{
      color: #e8e0d0;
      text-decoration: none;
      font-size: 0.98rem;
      min-width: 2.3rem;
    }}
    .ep-links a:hover {{ color: #c9a0b8; text-decoration: underline; }}
    .utility-buttons {{
      display: flex;
      flex-direction: column;
      gap: 0.85rem;
    }}
    .utility-button {{
      background: #1f1f1f;
      border: 1px solid #3a2030;
      color: #c9a0b8;
      text-decoration: none;
      padding: 0.95rem 1.1rem;
      border-radius: 4px;
      font-size: 1.08rem;
      text-align: center;
      letter-spacing: 0.04em;
    }}
    .utility-button:hover {{ background: #251520; }}
    @media (max-width: 760px) {{
      .index-layout {{
        grid-template-columns: 1fr;
      }}
      .utility-buttons {{
        order: -1;
      }}
    }}
  </style>
</head>
<body>
  <p class="subtitle">총 {len(episode_paths)}화 완성</p>

  <div class="index-layout">
    <div class="episode-sections">
      {ep_groups}
    </div>
    <div class="utility-buttons">
      {setting_links}
    </div>
  </div>
</body>
</html>'''

    os.makedirs(html_dir, exist_ok=True)
    with open(os.path.join(html_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    print('✓ html/index.html 생성 완료')


if __name__ == '__main__':
    for s in SETTING_FILES:
        build_setting(s['src'], s['out'], s['title'])
    build_game_page('관계망.md', 'setting/관계망.html', render_kangemang)
    build_game_page('연대기.md', 'setting/연대기.html', render_yondaegi)
    build_index()
