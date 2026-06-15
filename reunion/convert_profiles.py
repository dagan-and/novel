#!/usr/bin/env python3
"""convert-profile.js 의 Python 포팅 — 캐릭터 프로필 HTML + 인물 목록 생성"""
import sys, os, re, math

BASE = os.path.dirname(os.path.abspath(__file__))
EXCLUDE = {'캐릭터양식', '김시안'}

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
        '<polygon points="{}" fill="none" stroke="#3a2030" stroke-width="0.8"/>'.format(
            ' '.join(f'{pt(i, R*f)[0]:.1f},{pt(i, R*f)[1]:.1f}' for i in range(n))
        )
        for f in (0.25, 0.5, 0.75, 1.0)
    )

    axes = ''.join(
        '<line x1="{}" y1="{}" x2="{:.1f}" y2="{:.1f}" stroke="#3a2030" stroke-width="0.8"/>'.format(
            cx, cy, *pt(i, R)
        )
        for i in range(n)
    )

    raw_pts = [pt(i, max(3, R * s['value'] / 100)) for i, s in enumerate(stats)]
    data_poly = '<polygon points="{}" fill="rgba(201,160,184,0.2)" stroke="#c9a0b8" stroke-width="1.5"/>'.format(
        ' '.join(f'{x:.1f},{y:.1f}' for x, y in raw_pts)
    )
    dots = ''.join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#c9a0b8"/>'
        for x, y in raw_pts
    )

    LR = R + 24
    labels = []
    for i, s in enumerate(stats):
        x, y = pt(i, LR)
        anchor = 'end' if x < cx - 6 else ('start' if x > cx + 6 else 'middle')
        dy = -6 if y < cy - 6 else (12 if y > cy + 6 else 4)

        # 폰트 크기 기존 11.5 -> 20% 확대하여 약 13.8로 수정
        labels.append(
            f'<text x="{x:.1f}" y="{y+dy:.1f}" text-anchor="{anchor}" font-size="23.5" '
            f'fill="#a08090" font-family="\'Nanum Myeongjo\',Georgia,serif">'
            f'{s["label"]} <tspan fill="#c9a0b8">{s["value"]}</tspan></text>'
        )

    return (
        f'<svg class="emotion-chart" viewBox="-100 -25 500 360" xmlns="http://www.w3.org/2000/svg">'
        f'{grids}{axes}{data_poly}{dots}{"".join(labels)}</svg>'
    )

# ── 친밀도 파싱 ────────────────────────────────────────────────────
def parse_intimacy(raw):
    m = re.search(r'- 친밀도:\s*(.+)', raw)
    if not m:
        return 0
    mapping = {'깊은': 5, '가까움': 4, '보통': 3, '낮음': 2, '초기': 1}
    return mapping.get(m.group(1).strip(), 0)

# ── 관계 진도 파싱 ──────────────────────────────────────────────────
def parse_progress(raw):
    m = re.search(r'- 관계 진도:\s*(\d)단계', raw)
    return int(m.group(1)) if m else 0

# ── 친밀도 + 진도 상태 블록 ─────────────────────────────────────────
def build_status_block(intimacy, progress):
    if not intimacy and not progress:
        return ''

    hearts = ''.join(
        f'<span class="heart {"filled" if i <= intimacy else "empty"}">{"♥" if i <= intimacy else "♡"}</span>'
        for i in range(1, 6)
    )

    stage_labels = ['스킨십', '키스', '관계']
    stages = ''.join(
        '<div class="stage {cls}">'
        '<span class="stage-num">{n}단계</span>'
        '<span class="stage-dot">{dot}</span>'
        '<span class="stage-label">{label}</span>'
        '</div>'.format(
            cls='unlocked' if i <= progress else 'locked',
            n=i,
            dot='◆' if i <= progress else '◇',
            label=stage_labels[i - 1]
        )
        for i in range(1, 4)
    )

    return (
        '<div class="status-block">'
        f'<div class="status-hearts">{hearts}</div>'
        f'<div class="status-stages">{stages}</div>'
        '</div>'
    )

# ── 현재 구분 파싱 (부가설명 지우고 메인/서브만 추출) ────────────────
def get_category(raw):
    m = re.search(r'- 현재 구분:\s*(.+)', raw)
    if not m:
        return ''
    line = m.group(1)
    # 메인 또는 서브 글자만 정확하게 매칭해서 추출
    match = re.search(r'(메인|서브)', line)
    if match:
        return match.group(1)
    return line.strip()

# ── 프로필 HTML 빌드 ─────────────────────────────────────────────────
# 모든 폰트 크기(font-size)를 기존 대비 1.2배(20% 확대) 적용
PROFILE_CSS = """
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #1a1a1a;
      color: #e8e0d0;
      font-family: 'Nanum Myeongjo', Georgia, serif;
      font-size: 1.5rem; /* 1.0rem -> 1.2rem -> 1.5rem */
      line-height: 1.85;
      max-width: 820px;
      margin: 0 auto;
      padding: 3rem 1.5rem 5rem;
    }
    .header {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
      align-items: center;
      margin-bottom: 2.5rem;
      padding-bottom: 2rem;
      border-bottom: 1px solid #2a2a2a;
    }
    .portrait {
      width: 90%;
      max-width: 650px;
      border: 1px solid #3a2030;
      border-radius: 4px;
      overflow: hidden;
      background: #111;
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
      color: #444;
      font-size: 1.8rem; /* 1.2rem -> 1.44rem -> 1.8rem */
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
      border: 1px solid #3a2030;
      border-radius: 4px;
      box-shadow: 0 8px 40px rgba(0,0,0,0.7);
    }
    .header-info { text-align: center; }
    .header-info h1 {
      font-size: 3rem; /* 2rem -> 2.4rem -> 3rem */
      color: #c9a0b8;
      letter-spacing: 0.1em;
      margin-bottom: 0.4rem;
    }
    .category-tag {
      display: inline-block;
      background: #2a1020;
      color: #c9a0b8;
      border: 1px solid #3a2030;
      font-size: 1.18rem; /* 0.78rem -> 0.94rem -> 1.18rem */
      padding: 0.15rem 0.6rem;
      border-radius: 2px;
      letter-spacing: 0.05em;
    }
    .current-age {
      font-size: 1rem;
      color: #6a5060;
      letter-spacing: 0.05em;
      margin-top: 0.35rem;
    }
    h2 {
      font-size: 1.58rem; /* 1.05rem -> 1.26rem -> 1.58rem */
      color: #c9a0b8;
      margin: 2rem 0 0.6rem;
      padding-bottom: 0.3rem;
      border-bottom: 1px solid #2a2a2a;
      letter-spacing: 0.06em;
    }
    h3 { font-size: 1.43rem; /* 0.95rem -> 1.14rem -> 1.43rem */ color: #b08098; margin: 1.2rem 0 0.4rem; }
    p { margin: 0.5rem 0; }
    ul { padding-left: 1.4rem; margin: 0.4rem 0; }
    li { margin: 0.25rem 0; }
    hr { border: none; border-top: 1px solid #2a2a2a; margin: 1.6rem 0; }
    strong { color: #c8a8b8; }
    .back { display: inline-block; margin-bottom: 2rem; color: #c9a0b8; text-decoration: none; font-size: 1.33rem; /* 0.88rem -> 1.06rem -> 1.33rem */ }
    .back:hover { text-decoration: underline; }
    .emotion-chart { width: 90%; max-width: 380px; display: block; margin: 0 auto; }
    .status-block {
      text-align: center;
      margin: 1.4rem 0 0.4rem;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1rem;
    }
    .status-hearts { display: flex; gap: 0.3rem; }
    .heart { font-size: 1.7rem; line-height: 1; transition: transform 0.15s; }
    .heart.filled { color: #c9a0b8; }
    .heart.empty  { color: #2e2020; }
    .heart.filled:hover { transform: scale(1.2); }
    .status-stages { display: flex; gap: 1.4rem; }
    .stage {
      display: flex; flex-direction: column; align-items: center; gap: 0.3rem;
      font-family: 'Nanum Myeongjo', Georgia, serif;
    }
    .stage-num { font-size: 0.78rem; letter-spacing: 0.06em; }
    .stage-dot { font-size: 1.3rem; line-height: 1; }
    .stage-label { font-size: 0.72rem; letter-spacing: 0.04em; }
    .stage.unlocked .stage-dot  { color: #c9a0b8; }
    .stage.unlocked .stage-num  { color: #a08090; }
    .stage.unlocked .stage-label{ color: #a08090; }
    .stage.locked   .stage-dot  { color: #2e2020; }
    .stage.locked   .stage-num  { color: #333; }
    .stage.locked   .stage-label{ color: #2a2a2a; }
    @media (max-width: 560px) { .portrait { width: 100%; } .emotion-chart { max-width: 320px; } }
"""

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
    intimacy = parse_intimacy(raw)
    progress = parse_progress(raw)
    status_block = build_status_block(intimacy, progress)
    story_year, story_month = get_story_date()
    current_age = calc_current_age(raw, story_year, story_month)

    image_block = (
        f'<div class="portrait"><img src="{image_src}" alt="{name}" onclick="openLightbox(this.src)" /></div>'
        if image_src else
        f'<div class="portrait no-image"><span>{name}</span></div>'
    )

    body_md = re.sub(r'^# .+\n', '', raw)
    body_html = md_to_html(body_md)
    cat_tag = f'<span class="category-tag">{category}</span>' if category else ''
    age_tag = f'<p class="current-age">{story_year}년 기준 {current_age}세</p>' if current_age else ''

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>다시 만나는 관계들 — {name}</title>
  <style>{PROFILE_CSS}  </style>
</head>
<body>
  <a class="back" href="../characters.html">← 인물 목록</a>
  <div class="header">
    {image_block}
    {chart_block}
    {status_block}
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
        entries.append({'name': name, 'total_score': total_score, 'card': card})

    entries.sort(key=lambda e: -e['total_score'])
    grid = '\n    '.join(e['card'] for e in entries)

    html = f"""<!DOCTYPE html>
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
      font-size: 1.5rem; /* 리스트 페이지 기본 크기 추가 */
      max-width: 900px;
      margin: 0 auto;
      padding: 3rem 1.5rem 5rem;
    }}
    h1 {{ font-size: 2.4rem; /* 1.6rem -> 1.92rem -> 2.4rem */ color: #c9a0b8; text-align: center; margin-bottom: 3rem; letter-spacing: 0.08em; }}
    .grid {{ display: flex; flex-wrap: wrap; gap: 1rem; }}
    .card {{
      display: flex; flex-direction: column; align-items: center;
      text-decoration: none; color: #e8e0d0; width: 110px;
    }}
    .card img, .card .no-img {{
      width: 110px; height: 140px;
      object-fit: cover; object-position: top;
      border: 1px solid #3a2030; border-radius: 3px; background: #111;
    }}
    .card .no-img {{
      display: flex; align-items: center; justify-content: center;
      color: #555; font-size: 2.7rem; /* 1.8rem -> 2.16rem -> 2.7rem */
    }}
    .card span {{ margin-top: 0.4rem; font-size: 1.33rem; /* 0.88rem -> 1.06rem -> 1.33rem */ color: #c8a8b8; }}
    .card em {{ font-size: 1.13rem; /* 0.75rem -> 0.9rem -> 1.13rem */ color: #666; font-style: normal; }}
    .card:hover span {{ color: #c9a0b8; text-decoration: underline; }}
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