#!/usr/bin/env python3
"""convert-profile.js 의 Python 포팅 — 캐릭터 프로필 HTML + 인물 목록 생성"""
import sys, os, re, math
from pathlib import Path

from batch_paths import iter_episode_files

BASE = os.path.dirname(os.path.abspath(__file__))
EXCLUDE = {'캐릭터양식'}  # 주인공 이름 확정되면 여기 추가

# ── 스토리 현재 연도/월 파싱 (관계망.md 기준) ───────────────────────
def get_story_date():
    path = os.path.join(BASE, '관계망.md')
    if not os.path.exists(path):
        return None, None
    raw = open(path, encoding='utf-8').read()
    m = re.search(r'연도:\s*(\d{4})년\s*(\d{1,2})월', raw)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r'연도:\s*(\d{4})년', raw)
    return (int(m.group(1)), None) if m else (None, None)

# ── 현재 나이 계산 ───────────────────────────────────────────────────
def calc_current_age(raw, story_year, story_month):
    m = re.search(r'생년월일:\s*(\d{4})년', raw)
    if not m or not story_year:
        return None
    return story_year - int(m.group(1)) + 1

# ── 이미지 탐색 ─────────────────────────────────────────────────────
def find_image(name):
    for ext in ('png', 'jpg', 'jpeg', 'webp'):
        p = os.path.join(BASE, 'images', 'characters', f'{name}.{ext}')
        if os.path.exists(p):
            return f'../../images/characters/{name}.{ext}'
    return None

# ── 인라인 마크다운 ─────────────────────────────────────────────────
def inline_md(text):
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    return text

# ── 마크다운 → HTML ─────────────────────────────────────────────────
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

# ── 감정 수치 파싱 ──────────────────────────────────────────────────
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

# ── SVG 레이더 차트 ─────────────────────────────────────────────────
def build_radar_chart(stats):
    n = len(stats)
    cx, cy, R = 150, 150, 95
    TAU = 2 * math.pi
    offset = -math.pi / 2

    def pt(i, r):
        a = offset + (TAU * i) / n
        return (cx + r * math.cos(a), cy + r * math.sin(a))

    grids = ''.join(
        '<polygon points="{}" fill="none" stroke="#3d4a4c" stroke-width="0.8"/>'.format(
            ' '.join(f'{pt(i, R*f)[0]:.1f},{pt(i, R*f)[1]:.1f}' for i in range(n))
        )
        for f in (0.25, 0.5, 0.75, 1.0)
    )

    axes = ''.join(
        '<line x1="{}" y1="{}" x2="{:.1f}" y2="{:.1f}" stroke="#3d4a4c" stroke-width="0.8"/>'.format(
            cx, cy, *pt(i, R)
        )
        for i in range(n)
    )

    raw_pts = [pt(i, max(3, R * s['value'] / 100)) for i, s in enumerate(stats)]
    data_poly = '<polygon points="{}" fill="rgba(121,184,178,0.2)" stroke="#79b8b2" stroke-width="1.5"/>'.format(
        ' '.join(f'{x:.1f},{y:.1f}' for x, y in raw_pts)
    )
    dots = ''.join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#79b8b2"/>'
        for x, y in raw_pts
    )

    LR = R + 24
    labels = []
    for i, s in enumerate(stats):
        x, y = pt(i, LR)
        anchor = 'end' if x < cx - 6 else ('start' if x > cx + 6 else 'middle')
        dy = -6 if y < cy - 6 else (12 if y > cy + 6 else 4)

        labels.append(
            f'<text x="{x:.1f}" y="{y+dy:.1f}" text-anchor="{anchor}" font-size="22" '
            f'fill="#b7aca0" font-family="Pretendard,Noto Sans KR,Apple SD Gothic Neo,sans-serif">'
            f'{s["label"]} <tspan fill="#8fd0c9">{s["value"]}</tspan></text>'
        )

    return (
        f'<svg class="emotion-chart" viewBox="-100 -25 500 360" xmlns="http://www.w3.org/2000/svg">'
        f'{grids}{axes}{data_poly}{dots}{"".join(labels)}</svg>'
    )

# ── 성인씬 횟수 집계 ────────────────────────────────────────────────
def parse_profile_adult_scene_counts():
    counts = {}
    characters_dir = os.path.join(BASE, 'characters')
    if not os.path.exists(characters_dir):
        return counts

    for fname in sorted(os.listdir(characters_dir)):
        if not fname.endswith('.md'):
            continue
        name = os.path.splitext(fname)[0]
        if name == '캐릭터양식':
            continue

        raw = open(os.path.join(characters_dir, fname), encoding='utf-8').read()
        match = re.search(r'## \[성인씬 기록\][\s\S]*?- 총 성인씬:\s*(\d+)회', raw)
        if match:
            counts[name] = int(match.group(1))
    return counts


def parse_episode_adult_scene_counts():
    counts = {}
    episodes_dir = os.path.join(BASE, 'episodes')
    if not os.path.exists(episodes_dir):
        return counts

    for path in iter_episode_files(Path(episodes_dir), 'md'):
        lines = open(path, encoding='utf-8').read().splitlines()
        i = 0
        while i < len(lines):
            if '성인씬 #' not in lines[i]:
                i += 1
                continue

            i += 1
            in_people = False
            while i < len(lines) and lines[i].strip() != '---':
                line = lines[i]
                if line.startswith('- 등장인물:'):
                    in_people = True
                elif in_people and re.match(r'^- [^:]+:', line):
                    break
                elif in_people:
                    match = re.match(r'^\s{2,4}-\s*([가-힣]+):', line)
                    if match:
                        name = match.group(1)
                        if name not in {'외형 참고', '성격 참고'}:
                            counts[name] = counts.get(name, 0) + 1
                i += 1
            i += 1

    return counts


def parse_adult_scene_counts():
    profile_counts = parse_profile_adult_scene_counts()
    episode_counts = parse_episode_adult_scene_counts()
    return {**episode_counts, **profile_counts}


def build_adult_scene_block(count):
    hearts = ''.join(
        '<span class="heart filled">♥</span>'
        for _ in range(count)
    )
    if not hearts:
        hearts = '<span class="heart empty">♡</span>'
    return (
        '<div class="adult-scene-block">'
        f'<div class="adult-scene-hearts">{hearts}</div>'
        f'<p class="adult-scene-count">♥ {count}</p>'
        '</div>'
    )


def strip_hidden_profile_lines(body_md):
    hidden_patterns = (
        r'^- 친밀도:.*$',
        r'^- 관계 진도:.*$',
        r'^- 현재 단계:.*$',
    )
    for pattern in hidden_patterns:
        body_md = re.sub(pattern, '', body_md, flags=re.MULTILINE)
    return body_md

# ── 현재 구분 파싱 (부가설명/마크다운 표시 제거) ───────────────────
def get_category(raw):
    m = re.search(r'- 현재 구분:\s*(.+)', raw)
    if not m:
        return ''
    line = re.sub(r'[*_`]', '', m.group(1)).strip()
    # 메인 또는 서브 글자만 정확하게 매칭해서 추출
    match = re.search(r'(메인|서브)', line)
    if match:
        return match.group(1)
    return line

# ── 프로필 HTML 빌드 ─────────────────────────────────────────────────
PROFILE_CSS = """
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html { font-size: 120%; }
    body {
      background: #111417;
      color: #e8e1d5;
      font-family: 'Pretendard', 'Noto Sans KR', 'Apple SD Gothic Neo', sans-serif;
      font-size: 1.04rem;
      line-height: 1.82;
      max-width: 820px;
      margin: 0 auto;
      padding: 3rem 1.5rem 5rem;
      word-break: keep-all;
    }
    .header {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
      align-items: center;
      margin-bottom: 2.5rem;
      padding-bottom: 2rem;
      border-bottom: 1px solid #30383a;
    }
    .portrait {
      width: 90%;
      max-width: 650px;
      border: 1px solid #30383a;
      border-radius: 8px;
      overflow: hidden;
      background: #181d20;
    }
    .portrait img {
      width: 100%;
      height: auto;
      display: block;
      object-fit: cover;
      object-position: top;
      cursor: pointer;
      transition: opacity 0.15s;
    }
    .portrait img:hover { opacity: 0.85; }
    .portrait.no-image {
      display: flex;
      align-items: center;
      justify-content: center;
      color: #8f9996;
      font-size: 1.6rem;
      height: 200px;
    }
    #lightbox {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.88);
      z-index: 9999;
      align-items: center;
      justify-content: center;
      cursor: zoom-out;
    }
    #lightbox.open { display: flex; }
    #lightbox img {
      max-width: 90vw;
      max-height: 90vh;
      object-fit: contain;
      border: 1px solid #30383a;
      border-radius: 8px;
      box-shadow: 0 8px 40px rgba(0,0,0,0.7);
    }
    .header-info { text-align: center; }
    .header-info h1 {
      font-size: 3rem; /* 2rem -> 2.4rem -> 3rem */
      color: #79b8b2;
      letter-spacing: 0.02em;
      margin-bottom: 0.4rem;
    }
    .category-tag {
      display: inline-block;
      background: #20282b;
      color: #8fd0c9;
      border: 1px solid #3d4a4c;
      font-size: 0.92rem;
      padding: 0.18rem 0.62rem;
      border-radius: 999px;
      letter-spacing: 0.01em;
    }
    .current-age {
      font-size: 1rem;
      color: #9faaa6;
      letter-spacing: 0.01em;
      margin-top: 0.35rem;
    }
    h2 {
      font-size: 1.18rem;
      color: #79b8b2;
      margin: 2rem 0 0.6rem;
      padding-bottom: 0.3rem;
      border-bottom: 1px solid #30383a;
      letter-spacing: 0.01em;
    }
    h3 { font-size: 1.08rem; color: #d28a72; margin: 1.2rem 0 0.4rem; }
    p { margin: 0.5rem 0; }
    ul { padding-left: 1.4rem; margin: 0.4rem 0; }
    li { margin: 0.25rem 0; }
    hr { border: none; border-top: 1px solid #30383a; margin: 1.6rem 0; }
    strong { color: #d28a72; }
    code { background: #20282b; color: #8fd0c9; padding: 0.1rem 0.35rem; border-radius: 4px; }
    .back { display: inline-block; margin-bottom: 2rem; color: #8fd0c9; text-decoration: none; font-size: 1rem; font-weight: 700; }
    .back:hover { text-decoration: underline; }
    .emotion-chart { width: 90%; max-width: 380px; display: block; margin: 0 auto; }
    .adult-scene-block {
      text-align: center;
      margin: 1.4rem 0 0.4rem;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.55rem;
    }
    .adult-scene-hearts {
      display: flex;
      gap: 0.3rem;
      flex-wrap: wrap;
      justify-content: center;
    }
    .heart { font-size: 1.45rem; line-height: 1; }
    .heart.filled { color: #d97b95; }
    .heart.empty  { color: #30383a; }
    .adult-scene-count {
      margin: 0;
      color: #d97b95;
      font-size: 0.95rem;
      letter-spacing: 0.03em;
    }
    @media (max-width: 560px) { .portrait { width: 100%; } .emotion-chart { max-width: 320px; } }
"""

ADULT_SCENE_COUNTS = parse_adult_scene_counts()

def build_profile(name):
    file = os.path.join(BASE, 'characters', f'{name}.md')
    if not os.path.exists(file):
        print(f'캐릭터 없음: {name}')
        return False

    raw = open(file, encoding='utf-8').read()
    image_src = find_image(name)
    category = get_category(raw)
    emotion_stats = parse_emotion_stats(raw)
    chart_block = build_radar_chart(emotion_stats) if emotion_stats else ''
    adult_scene_block = build_adult_scene_block(ADULT_SCENE_COUNTS.get(name, 0))
    story_year, story_month = get_story_date()
    current_age = calc_current_age(raw, story_year, story_month)

    image_block = (
        f'<div class="portrait"><img src="{image_src}" alt="{name}" onclick="openLightbox(this.src)" /></div>'
        if image_src else
        f'<div class="portrait no-image"><span>{name}</span></div>'
    )

    body_md = re.sub(r'^# .+\n', '', raw)
    body_md = strip_hidden_profile_lines(body_md)
    body_html = md_to_html(body_md)
    cat_tag = f'<span class="category-tag">{category}</span>' if category else ''
    age_tag = f'<p class="current-age">{story_year}년 기준 {current_age}세</p>' if current_age else ''

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name}</title>
  <style>{PROFILE_CSS}  </style>
</head>
<body>
  <a class="back" href="../characters.html">← 인물 목록</a>
  <div class="header">
    {image_block}
    {chart_block}
    {adult_scene_block}
    <div class="header-info">
      <h1>{name}</h1>
      {cat_tag}
      {age_tag}
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
</html>"""

    out_dir = os.path.join(BASE, 'html', 'characters')
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f'{name}.html')
    open(out_file, 'w', encoding='utf-8').write(html)
    print(f'✓ html/characters/{name}.html 생성 완료')
    return True

# ── 인물 목록 index ─────────────────────────────────────────────────
# 인물 목록 페이지 내부 텍스트 크기도 1.2배(20% 확대) 일괄 적용
def build_index(names):
    entries = []
    for name in names:
        file = os.path.join(BASE, 'characters', f'{name}.md')
        raw = open(file, encoding='utf-8').read() if os.path.exists(file) else ''
        category = get_category(raw)
        stats = parse_emotion_stats(raw)
        total_score = sum(s['value'] for s in stats) if stats else 0
        img_src = find_image(name)
        if img_src:
            img_from_index = '../' + img_src.replace('../../', '')
            thumb = f'<img src="{img_from_index}" alt="{name}">'
        else:
            thumb = f'<div class="no-img">{name[0]}</div>'
        cat_em = f'<em>{category}</em>' if category else ''
        card = f'<a class="card" href="characters/{name}.html">{thumb}<span>{name}</span>{cat_em}</a>'
        adult_count = ADULT_SCENE_COUNTS.get(name, 0)
        entries.append({'name': name, 'total_score': total_score, 'adult_count': adult_count, 'card': card})

    entries.sort(key=lambda e: (-e['adult_count'], -e['total_score']))
    grid = '\n    '.join(e['card'] for e in entries)

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>인물</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html {{ font-size: 120%; }}
    body {{
      background: #111417;
      color: #e8e1d5;
      font-family: 'Pretendard', 'Noto Sans KR', 'Apple SD Gothic Neo', sans-serif;
      font-size: 1rem;
      width: 100%;
      height: 100vh;
      height: 100svh;
      height: 100dvh;
      margin: 0 auto;
      padding: 1.2rem 1.5rem max(1.2rem, env(safe-area-inset-bottom));
      word-break: keep-all;
      overflow: hidden;
    }}
    h1 {{ font-size: 1.8rem; color: #79b8b2; text-align: center; margin-bottom: 3rem; letter-spacing: 0.02em; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      grid-template-rows: repeat(2, minmax(0, 1fr));
      gap: 0.9rem;
      height: 100%;
    }}
    .card {{
      display: flex; flex-direction: column; justify-content: flex-end;
      text-decoration: none; color: #e8e1d5;
      min-height: 0;
      overflow: hidden;
      position: relative;
      border: 1px solid #30383a;
      border-radius: 8px;
      background:
        linear-gradient(180deg, rgba(17,20,23,0) 22%, rgba(17,20,23,0.72) 70%, rgba(17,20,23,0.96) 100%),
        #181d20;
      box-shadow: 0 18px 38px rgba(0,0,0,0.28);
    }}
    .card img, .card .no-img {{
      position: absolute;
      inset: 0;
      width: 100%; height: 100%;
      object-fit: cover; object-position: top;
      border: 0; border-radius: 0; background: #181d20;
      transition: transform 0.24s ease, filter 0.24s ease;
    }}
    .card .no-img {{
      display: flex; align-items: center; justify-content: center;
      color: #8f9996; font-size: 3rem;
    }}
    .card span, .card em {{ position: relative; z-index: 1; margin-left: 1rem; margin-right: 1rem; }}
    .card span, .card em {{
      -webkit-text-stroke: 0.45px rgba(0,0,0,0.9);
      text-shadow: 0 1px 2px rgba(0,0,0,1), 0 3px 12px rgba(0,0,0,0.95);
    }}
    .card span {{ margin-bottom: 0.12rem; font-size: 1.22rem; color: #f2fffb; font-weight: 900; }}
    .card em {{ margin-bottom: 1rem; font-size: 0.9rem; color: #e3eee9; font-style: normal; font-weight: 700; }}
    .card:hover img {{ transform: scale(1.035); filter: brightness(1.08); }}
    .card:hover span {{ color: #8fd0c9; text-decoration: underline; }}
    @media (max-width: 760px) {{
      body {{ padding: 0.75rem 0.55rem max(0.75rem, env(safe-area-inset-bottom)); }}
      .grid {{ gap: 0.45rem; }}
      .card span, .card em {{ margin-left: 0.55rem; margin-right: 0.55rem; }}
      .card span {{ font-size: clamp(0.8rem, 3.6vw, 1.05rem); }}
      .card em {{ margin-bottom: 0.55rem; font-size: clamp(0.68rem, 3vw, 0.82rem); }}
    }}
    @media (max-width: 460px) {{
      body {{ padding: 0.55rem 0.35rem max(0.55rem, env(safe-area-inset-bottom)); }}
      .grid {{ gap: 0.35rem; }}
    }}
  </style>
</head>
<body>
  <div class="grid">
    {grid}
  </div>
</body>
</html>"""

    out_file = os.path.join(BASE, 'html', 'characters.html')
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    open(out_file, 'w', encoding='utf-8').write(html)
    print('✓ html/characters.html (인물 목록) 생성 완료')

# ── 실행 ────────────────────────────────────────────────────────────
def build_all():
    char_dir = os.path.join(BASE, 'characters')
    names = sorted([
        f.replace('.md', '')
        for f in os.listdir(char_dir)
        if f.endswith('.md') and f.replace('.md', '') not in EXCLUDE
    ])
    count = sum(1 for n in names if build_profile(n))
    print(f'\n총 {count}개 프로필 생성 완료')
    build_index(names)

arg = sys.argv[1] if len(sys.argv) > 1 else 'all'
if arg == 'all':
    build_all()
else:
    if not build_profile(arg):
        sys.exit(1)
