#!/usr/bin/env python3
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SETTING_FILES = [
    {'src': '관계망.md',         'out': 'setting/관계망.html',   'title': '관계망'},
    {'src': '연대기.md',         'out': 'setting/연대기.html',   'title': '연대기'},
    {'src': 'setting/세계관.md', 'out': 'setting/세계관.html',   'title': '세계관'},
]

DARK_STYLE = """
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #1a1a1a;
      color: #e8e0d0;
      font-family: 'Nanum Myeongjo', Georgia, serif;
      font-size: 0.97rem;
      line-height: 1.85;
      max-width: 960px;
      margin: 0 auto;
      padding: 3rem 1.5rem 5rem;
      word-break: keep-all;
    }
    h1 { font-size: 1.5rem; color: #c9a0b8; margin-bottom: 2rem; letter-spacing: 0.08em; }
    h2 { font-size: 1.05rem; color: #c9a0b8; margin: 2.2rem 0 0.7rem; padding-bottom: 0.3rem; border-bottom: 1px solid #2a2a2a; letter-spacing: 0.05em; }
    h3 { font-size: 0.95rem; color: #b08098; margin: 1.4rem 0 0.4rem; }
    p { margin: 0.5rem 0; }
    ul { padding-left: 1.4rem; margin: 0.4rem 0; }
    li { margin: 0.25rem 0; }
    hr { border: none; border-top: 1px solid #2a2a2a; margin: 1.8rem 0; }
    strong { color: #c8a8b8; }
    em { color: #a0a0a0; font-style: italic; }
    blockquote { border-left: 3px solid #3a2030; padding-left: 1rem; color: #a0a0a0; margin: 0.8rem 0; }
    .table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; margin: 1rem 0; }
    table { width: max-content; min-width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    th { background: #222; color: #c9a0b8; padding: 0.5rem 0.75rem; text-align: left; border-bottom: 1px solid #3a2030; white-space: nowrap; }
    td { padding: 0.45rem 0.75rem; border-bottom: 1px solid #252525; vertical-align: top; }
    tr:hover td { background: #1f1f1f; }
    code { background: #222; color: #c9a0b8; padding: 0.1rem 0.35rem; border-radius: 2px; font-size: 0.88rem; }
    .back { display: inline-block; margin-bottom: 2rem; color: #c9a0b8; text-decoration: none; font-size: 0.88rem; }
    .back:hover { text-decoration: underline; }
"""


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


def build_setting(src, out, title):
    src_path = os.path.join(BASE_DIR, src)
    if not os.path.exists(src_path):
        print(f'건너뜀: {src} 없음')
        return

    with open(src_path, encoding='utf-8') as f:
        raw = f.read()

    body = md_to_html(raw)

    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>다시 만나는 관계들 — {title}</title>
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


def build_index():
    html_dir = os.path.join(BASE_DIR, 'html')
    ep_files = []
    if os.path.exists(html_dir):
        ep_files = sorted(
            [f for f in os.listdir(html_dir) if re.match(r'^ep\.\d+\.html$', f)],
            key=lambda f: int(re.search(r'\d+', f).group())
        )

    grouped = [ep_files[i:i + 10] for i in range(0, len(ep_files), 10)]
    ep_groups = ''
    for gi, group in enumerate(grouped):
        start = gi * 10 + 1
        end = min(start + 9, len(ep_files))
        links = ''.join(
            '<a href="{}">{}</a>'.format(f, int(re.search(r'\d+', f).group()))
            for f in group
        )
        ep_groups += f'<div class="ep-group"><div class="ep-label">{start}~{end}화</div><div class="ep-links">{links}</div></div>'

    setting_links = '\n      '.join(
        '<a class="setting-card" href="{out}">{title}</a>'.format(**s)
        for s in SETTING_FILES
    )
    ep_section = ep_groups if ep_groups else '<p style="color:#555;font-size:0.88rem;">에피소드 없음</p>'

    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>다시 만나는 관계들</title>
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
    h1 {{ font-size: 2rem; color: #c9a0b8; text-align: center; letter-spacing: 0.12em; margin-bottom: 0.5rem; }}
    .subtitle {{ text-align: center; color: #666; font-size: 0.85rem; margin-bottom: 3rem; }}
    section {{ margin-bottom: 2.8rem; }}
    h2 {{ font-size: 0.85rem; color: #888; letter-spacing: 0.12em; margin-bottom: 1rem; padding-bottom: 0.35rem; border-bottom: 1px solid #2a2a2a; }}
    .setting-grid {{ display: flex; gap: 1rem; flex-wrap: wrap; }}
    .setting-card {{
      flex: 1; min-width: 140px;
      background: #1f1f1f; border: 1px solid #3a2030;
      color: #c9a0b8; text-decoration: none;
      padding: 0.9rem 1.2rem;
      border-radius: 3px; font-size: 0.9rem;
      text-align: center; letter-spacing: 0.04em;
    }}
    .setting-card:hover {{ background: #251520; }}
    .char-link {{
      display: inline-block;
      background: #1f1f1f; border: 1px solid #3a2030;
      color: #c9a0b8; text-decoration: none;
      padding: 0.9rem 2rem; border-radius: 3px; font-size: 0.9rem;
    }}
    .char-link:hover {{ background: #251520; }}
    .ep-group {{ margin-bottom: 1rem; }}
    .ep-label {{ font-size: 0.75rem; color: #666; margin-bottom: 0.35rem; letter-spacing: 0.05em; }}
    .ep-links {{ display: flex; flex-wrap: wrap; gap: 0.4rem; }}
    .ep-links a {{
      display: inline-block;
      width: 48px; text-align: center;
      background: #1f1f1f; border: 1px solid #2a2a2a;
      color: #c8a8b8; text-decoration: none;
      padding: 0.3rem 0; font-size: 0.82rem;
      border-radius: 2px;
    }}
    .ep-links a:hover {{ background: #251520; color: #c9a0b8; }}
  </style>
</head>
<body>
  <h1>다시 만나는 관계들</h1>
  <p class="subtitle">총 {len(ep_files)}화 완성</p>

  <section>
    <h2>설정</h2>
    <div class="setting-grid">
      {setting_links}
    </div>
  </section>

  <section>
    <h2>인물</h2>
    <a class="char-link" href="characters.html">인물 목록 →</a>
  </section>

  <section>
    <h2>에피소드</h2>
    {ep_section}
  </section>
</body>
</html>'''

    os.makedirs(html_dir, exist_ok=True)
    with open(os.path.join(html_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    print('✓ html/index.html 생성 완료')


if __name__ == '__main__':
    for s in SETTING_FILES:
        build_setting(s['src'], s['out'], s['title'])
    build_index()
