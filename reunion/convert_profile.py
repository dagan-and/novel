#!/usr/bin/env python3
import os
import sys
import re
import math

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCLUDE = {'캐릭터양식', '김시안'}


def find_image(name):
    for ext in ['png', 'jpg', 'jpeg', 'webp']:
        p = os.path.join(BASE_DIR, 'images', 'characters', f'{name}.{ext}')
        if os.path.exists(p):
            return f'../../images/characters/{name}.{ext}'
    return None


def inline_md(text):
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    return text


def md_to_html(text):
    lines = text.split('\n')
    out = []
    in_ul = False

    for line in lines:
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
        elif not line.strip():
            out.append('')
        else:
            out.append(f'<p>{inline_md(line)}</p>')

    if in_ul:
        out.append('</ul>')
    return '\n'.join(out)


def get_category(raw):
    m = re.search(r'- 현재 구분:\s*(.+)', raw)
    if not m:
        return ''
    cat = re.sub(r'\s*/\s*메인|\s*/\s*서브', '', m.group(1).strip())
    return cat.strip()


def parse_emotion_stats(raw):
    m = re.search(r'### 감정 수치([\s\S]*?)(?=\n##|\n#|$)', raw)
    if not m:
        return None
    stats = []
    for line in m.group(1).split('\n'):
        hit = re.match(r'^- (.+?):\s*(\d+)/100', line)
        if hit:
            stats.append({'label': hit.group(1).strip(), 'value': int(hit.group(2))})
    return stats if len(stats) >= 3 else None


def build_radar_chart(stats):
    n = len(stats)
    cx, cy, R = 150, 150, 95
    TAU = 2 * math.pi
    offset = -math.pi / 2

    def pt(i, r):
        a = offset + (TAU * i) / n
        return (cx + r * math.cos(a), cy + r * math.sin(a))

    grids = ''
    for f in [0.25, 0.5, 0.75, 1.0]:
        pts = ' '.join('{:.1f},{:.1f}'.format(*pt(i, R * f)) for i in range(n))
        grids += f'<polygon points="{pts}" fill="none" stroke="#3a2030" stroke-width="0.8"/>'

    axes = ''
    for i in range(n):
        x, y = pt(i, R)
        axes += f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#3a2030" stroke-width="0.8"/>'

    raw_pts = [pt(i, max(3, R * s['value'] / 100)) for i, s in enumerate(stats)]
    data_pts = ' '.join('{:.1f},{:.1f}'.format(x, y) for x, y in raw_pts)
    data_poly = f'<polygon points="{data_pts}" fill="rgba(201,160,184,0.2)" stroke="#c9a0b8" stroke-width="1.5"/>'
    dots = ''.join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#c9a0b8"/>' for x, y in raw_pts)

    LR = R + 24
    labels = ''
    for i, s in enumerate(stats):
        x, y = pt(i, LR)
        anchor = 'end' if x < cx - 6 else ('start' if x > cx + 6 else 'middle')
        dy = -6 if y < cy - 6 else (12 if y > cy + 6 else 4)
        labels += (
            f'<text x="{x:.1f}" y="{y+dy:.1f}" text-anchor="{anchor}" '
            f'font-size="11.5" fill="#a08090" '
            f'font-family="\'Nanum Myeongjo\',Georgia,serif">'
            f'{s["label"]} <tspan fill="#c9a0b8">{s["value"]}</tspan></text>'
        )

    return (
        f'<svg class="emotion-chart" viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">'
        f'{grids}{axes}{data_poly}{dots}{labels}</svg>'
    )


def build_profile(name):
    file_path = os.path.join(BASE_DIR, 'characters', f'{name}.md')
    if not os.path.exists(file_path):
        print(f'캐릭터 없음: {name}', file=sys.stderr)
        return False

    with open(file_path, encoding='utf-8') as f:
        raw = f.read()

    image_src = find_image(name)
    category = get_category(raw)
    emotion_stats = parse_emotion_stats(raw)
    chart_block = build_radar_chart(emotion_stats) if emotion_stats else ''

    if image_src:
        image_block = f'<div class="portrait"><img src="{image_src}" alt="{name}" onclick="openLightbox(this.src)" /></div>'
    else:
        image_block = f'<div class="portrait no-image"><span>{name}</span></div>'

    body_md = re.sub(r'^# .+\n', '', raw)
    body_html = md_to_html(body_md)
    cat_tag = f'<span class="category-tag">{category}</span>' if category else ''

    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>다시 만나는 관계들 — {name}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #1a1a1a;
      color: #e8e0d0;
      font-family: 'Nanum Myeongjo', Georgia, serif;
      font-size: 1.0rem;
      line-height: 1.85;
      max-width: 820px;
      margin: 0 auto;
      padding: 3rem 1.5rem 5rem;
    }}
    .header {{
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
      align-items: center;
      margin-bottom: 2.5rem;
      padding-bottom: 2rem;
      border-bottom: 1px solid #2a2a2a;
    }}
    .portrait {{
      width: 90%;
      max-width: 650px;
      border: 1px solid #3a2030;
      border-radius: 4px;
      overflow: hidden;
      background: #111;
    }}
    .portrait img {{
      width: 100%;
      height: auto;
      display: block;
      object-fit: cover;
      object-position: top;
      cursor: pointer;
      transition: opacity 0.15s;
    }}
    .portrait img:hover {{ opacity: 0.85; }}
    .portrait.no-image {{
      display: flex;
      align-items: center;
      justify-content: center;
      color: #444;
      font-size: 1.2rem;
      height: 200px;
    }}
    #lightbox {{
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.88);
      z-index: 9999;
      align-items: center;
      justify-content: center;
      cursor: zoom-out;
    }}
    #lightbox.open {{ display: flex; }}
    #lightbox img {{
      max-width: 90vw;
      max-height: 90vh;
      object-fit: contain;
      border: 1px solid #3a2030;
      border-radius: 4px;
      box-shadow: 0 8px 40px rgba(0,0,0,0.7);
    }}
    .header-info {{ text-align: center; }}
    .header-info h1 {{
      font-size: 2rem;
      color: #c9a0b8;
      letter-spacing: 0.1em;
      margin-bottom: 0.4rem;
    }}
    .category-tag {{
      display: inline-block;
      background: #2a1020;
      color: #c9a0b8;
      border: 1px solid #3a2030;
      font-size: 0.78rem;
      padding: 0.15rem 0.6rem;
      border-radius: 2px;
      letter-spacing: 0.05em;
    }}
    h2 {{
      font-size: 1.05rem;
      color: #c9a0b8;
      margin: 2rem 0 0.6rem;
      padding-bottom: 0.3rem;
      border-bottom: 1px solid #2a2a2a;
      letter-spacing: 0.06em;
    }}
    h3 {{ font-size: 0.95rem; color: #b08098; margin: 1.2rem 0 0.4rem; }}
    p {{ margin: 0.5rem 0; }}
    ul {{ padding-left: 1.4rem; margin: 0.4rem 0; }}
    li {{ margin: 0.25rem 0; }}
    hr {{ border: none; border-top: 1px solid #2a2a2a; margin: 1.6rem 0; }}
    strong {{ color: #c8a8b8; }}
    .emotion-chart {{
      width: 90%;
      max-width: 300px;
      display: block;
      margin: 0 auto;
    }}
    .back {{
      display: inline-block;
      margin-bottom: 2rem;
      color: #c9a0b8;
      text-decoration: none;
      font-size: 0.88rem;
    }}
    .back:hover {{ text-decoration: underline; }}
    @media (max-width: 560px) {{
      .portrait {{ width: 100%; }}
      .emotion-chart {{ max-width: 260px; }}
    }}
  </style>
</head>
<body>
  <a class="back" href="../characters.html">← 인물 목록</a>
  <div class="header">
    {image_block}
    {chart_block}
    <div class="header-info">
      <h1>{name}</h1>
      {cat_tag}
    </div>
  </div>
  <div class="profile-body">
    {body_html}
  </div>
  <div id="lightbox" onclick="closeLightbox()">
    <img id="lightbox-img" src="" alt="">
  </div>
  <script>
    function openLightbox(src) {{
      document.getElementById('lightbox-img').src = src;
      document.getElementById('lightbox').classList.add('open');
    }}
    function closeLightbox() {{
      document.getElementById('lightbox').classList.remove('open');
    }}
    document.addEventListener('keydown', function(e) {{
      if (e.key === 'Escape') closeLightbox();
    }});
  </script>
</body>
</html>'''

    out_dir = os.path.join(BASE_DIR, 'html', 'characters')
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, f'{name}.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'✓ html/characters/{name}.html 생성 완료')
    return True


def build_all():
    dir_path = os.path.join(BASE_DIR, 'characters')
    if not os.path.exists(dir_path):
        print('characters/ 디렉토리 없음', file=sys.stderr)
        return

    names = sorted(
        f[:-3] for f in os.listdir(dir_path)
        if f.endswith('.md') and f[:-3] not in EXCLUDE
    )

    count = sum(1 for name in names if build_profile(name))
    print(f'\n총 {count}개 프로필 생성 완료')
    build_index(names)


def build_index(names):
    dir_path = os.path.join(BASE_DIR, 'characters')
    entries = []

    for name in names:
        file_path = os.path.join(dir_path, f'{name}.md')
        raw = open(file_path, encoding='utf-8').read() if os.path.exists(file_path) else ''
        category = get_category(raw)
        stats = parse_emotion_stats(raw)
        total_score = sum(s['value'] for s in stats) if stats else 0
        img_src = find_image(name)
        thumb = (
            '<img src="../{}" alt="{}">'.format(img_src.replace('../../', ''), name)
            if img_src else
            '<div class="no-img">{}</div>'.format(name[0])
        )
        cat_em = f'<em>{category}</em>' if category else ''
        card = f'<a class="card" href="characters/{name}.html">{thumb}<span>{name}</span>{cat_em}</a>'
        entries.append({'total_score': total_score, 'card': card})

    entries.sort(key=lambda e: e['total_score'], reverse=True)
    grid_html = '<div class="grid">{}</div>'.format(''.join(e['card'] for e in entries))

    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>다시 만나는 관계들 — 인물</title>
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
    h1 {{ font-size: 1.6rem; color: #c9a0b8; text-align: center; margin-bottom: 3rem; letter-spacing: 0.08em; }}
    .grid {{ display: flex; flex-wrap: wrap; gap: 1rem; }}
    .card {{
      display: flex;
      flex-direction: column;
      align-items: center;
      text-decoration: none;
      color: #e8e0d0;
      width: 110px;
    }}
    .card img, .card .no-img {{
      width: 110px;
      height: 140px;
      object-fit: cover;
      object-position: top;
      border: 1px solid #3a2030;
      border-radius: 3px;
      background: #111;
    }}
    .card .no-img {{
      display: flex;
      align-items: center;
      justify-content: center;
      color: #555;
      font-size: 1.8rem;
    }}
    .card span {{ margin-top: 0.4rem; font-size: 0.88rem; color: #c8a8b8; }}
    .card em {{ font-size: 0.75rem; color: #666; font-style: normal; }}
    .card:hover span {{ color: #c9a0b8; text-decoration: underline; }}
  </style>
</head>
<body>
  <h1>다시 만나는 관계들 — 인물</h1>
  {grid_html}
</body>
</html>'''

    out_file = os.path.join(BASE_DIR, 'html', 'characters.html')
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print('✓ html/characters.html (인물 목록) 생성 완료')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('사용법: python3 convert_profile.py {이름} | all', file=sys.stderr)
        sys.exit(1)
    arg = sys.argv[1]
    if arg == 'all':
        build_all()
    else:
        if not build_profile(arg):
            sys.exit(1)
