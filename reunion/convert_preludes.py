#!/usr/bin/env python3
"""
convert_preludes.py — preludes.html 생성
  - 상단: 좌우 스크롤 가능한 삽화 갤러리
  - 하단: 인물 초상화 그리드
"""

import os, re, unicodedata

def nfc(s):
    return unicodedata.normalize('NFC', s)

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
IMG_PRE   = os.path.join(BASE_DIR, 'images', 'preludes')
IMG_CHAR  = os.path.join(BASE_DIR, 'images', 'characters')
CHAR_HTML = os.path.join(BASE_DIR, 'html', 'characters')
OUT_FILE  = os.path.join(BASE_DIR, 'html', 'preludes.html')

# 인물 순서 (characters.html 기준)
CHAR_ORDER = ['이하은', '한서진', '임소율', '정다온', '박미현', '오연서', '배수인', '김시안']
CHAR_ROLE  = {'이하은': '메인', '한서진': '메인', '임소율': '메인', '정다온': '메인',
              '박미현': '서브', '오연서': '서브', '배수인': '서브', '김시안': '메인'}


def collect_preludes():
    """images/preludes/ 에서 NNN.png 목록 수집 → (ep_num, filename) 정렬"""
    items = []
    for f in sorted(os.listdir(IMG_PRE)):
        m = re.match(r'^(\d+)\.png$', f)
        if m:
            items.append((int(m.group(1)), f))
    return items


def collect_characters():
    """images/characters/ 에 이미지가 있는 인물만 (CHAR_ORDER 순)"""
    result = []
    existing_imgs = {nfc(os.path.splitext(f)[0]) for f in os.listdir(IMG_CHAR) if f.endswith('.png')}
    existing_html = {nfc(os.path.splitext(f)[0]) for f in os.listdir(CHAR_HTML) if f.endswith('.html')}
    for name in CHAR_ORDER:
        if name in existing_imgs:
            has_profile = name in existing_html
            result.append({'name': name, 'has_profile': has_profile, 'role': CHAR_ROLE.get(name, '')})
    return result


def build_prelude_items(preludes):
    lines = []
    for ep_num, fname in preludes:
        ep_id  = f'ep.{ep_num:03d}'
        ep_href = f'{ep_id}.html'
        lines.append(
            f'      <a class="prelude-item" href="{ep_href}">\n'
            f'        <img src="../images/preludes/{fname}" alt="{ep_id} 삽화" loading="lazy">\n'
            f'        <span>{ep_id}</span>\n'
            f'      </a>'
        )
    return '\n'.join(lines)


def build_char_items(chars):
    lines = []
    for c in chars:
        name = c['name']
        role = c['role']
        img_src = f'../images/characters/{name}.png'
        if c['has_profile']:
            tag_open  = f'<a class="char-card" href="characters/{name}.html">'
            tag_close = '</a>'
        else:
            tag_open  = '<div class="char-card">'
            tag_close = '</div>'
        lines.append(
            f'    {tag_open}\n'
            f'      <img src="{img_src}" alt="{name}">\n'
            f'      <span>{name}</span>\n'
            f'      <em>{role}</em>\n'
            f'    {tag_close}'
        )
    return '\n'.join(lines)


HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>다시 만나는 관계들 — 삽화</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #1a1a1a;
      color: #e8e0d0;
      font-family: 'Nanum Myeongjo', Georgia, serif;
      max-width: 960px;
      margin: 0 auto;
      padding: 3rem 1.5rem 5rem;
    }}
    a.back {{
      display: inline-block; margin-bottom: 2.5rem;
      color: #c9a0b8; text-decoration: none; font-size: 1.05rem;
    }}
    a.back:hover {{ text-decoration: underline; }}
    h1 {{
      font-size: 2.2rem; color: #c9a0b8; text-align: center;
      letter-spacing: 0.1em; margin-bottom: 0.4rem;
    }}
    .page-sub {{
      text-align: center; color: #666; font-size: 1rem; margin-bottom: 3rem;
    }}

    /* ── 섹션 헤더 ── */
    .section-title {{
      font-size: 1rem; color: #888; letter-spacing: 0.12em;
      margin-bottom: 1.2rem; padding-bottom: 0.35rem;
      border-bottom: 1px solid #2a2a2a;
    }}

    /* ── 삽화 스크롤 영역 ── */
    .gallery-wrap {{
      position: relative;
      margin-bottom: 3.5rem;
    }}
    .gallery-track {{
      display: flex;
      gap: 1rem;
      overflow-x: auto;
      scroll-snap-type: x mandatory;
      -webkit-overflow-scrolling: touch;
      padding: 0.5rem 0 1rem;
      scrollbar-width: thin;
      scrollbar-color: #3a2030 #1a1a1a;
    }}
    .gallery-track::-webkit-scrollbar {{ height: 5px; }}
    .gallery-track::-webkit-scrollbar-track {{ background: #1a1a1a; }}
    .gallery-track::-webkit-scrollbar-thumb {{ background: #3a2030; border-radius: 3px; }}

    .prelude-item {{
      flex: 0 0 auto;
      scroll-snap-align: start;
      display: flex; flex-direction: column; align-items: center;
      text-decoration: none; color: #e8e0d0;
      width: 220px;
    }}
    .prelude-item img {{
      width: 220px; height: 310px;
      object-fit: cover; object-position: top;
      border: 1px solid #3a2030; border-radius: 3px;
      background: #111;
      transition: border-color 0.2s;
    }}
    .prelude-item:hover img {{ border-color: #c9a0b8; }}
    .prelude-item span {{
      margin-top: 0.45rem; font-size: 0.95rem; color: #888;
      letter-spacing: 0.05em;
    }}
    .prelude-item:hover span {{ color: #c9a0b8; }}

    /* 좌우 버튼 */
    .scroll-btn {{
      position: absolute; top: 50%; transform: translateY(-60%);
      background: rgba(26,26,26,0.85); border: 1px solid #3a2030;
      color: #c9a0b8; font-size: 1.8rem; line-height: 1;
      width: 2.4rem; height: 2.4rem; border-radius: 50%;
      cursor: pointer; display: flex; align-items: center; justify-content: center;
      z-index: 2; user-select: none;
      transition: background 0.2s, border-color 0.2s;
    }}
    .scroll-btn:hover {{ background: #251520; border-color: #c9a0b8; }}
    .scroll-btn.left  {{ left: -1.3rem; }}
    .scroll-btn.right {{ right: -1.3rem; }}

    /* ── 인물 그리드 ── */
    .char-grid {{
      display: flex; flex-wrap: wrap; gap: 1rem;
    }}
    .char-card {{
      display: flex; flex-direction: column; align-items: center;
      text-decoration: none; color: #e8e0d0; width: 110px;
    }}
    .char-card img {{
      width: 110px; height: 140px;
      object-fit: cover; object-position: top;
      border: 1px solid #3a2030; border-radius: 3px; background: #111;
      transition: border-color 0.2s;
    }}
    .char-card:hover img {{ border-color: #c9a0b8; }}
    .char-card span {{ margin-top: 0.4rem; font-size: 1.05rem; color: #c8a8b8; }}
    .char-card em {{ font-size: 0.88rem; color: #666; font-style: normal; }}
    .char-card:hover span {{ color: #c9a0b8; text-decoration: underline; }}
  </style>
</head>
<body>

  <a class="back" href="index.html">← 목차</a>

  <h1>다시 만나는 관계들</h1>
  <p class="page-sub">삽화 {count}장 · 인물 {char_count}명</p>

  <h2 class="section-title">삽화</h2>
  <div class="gallery-wrap">
    <button class="scroll-btn left"  id="btn-left"  aria-label="이전">&#8249;</button>
    <div class="gallery-track" id="gallery-track">
{prelude_items}
    </div>
    <button class="scroll-btn right" id="btn-right" aria-label="다음">&#8250;</button>
  </div>

  <h2 class="section-title">인물</h2>
  <div class="char-grid">
{char_items}
  </div>

  <script>
    const track = document.getElementById('gallery-track');
    const STEP  = 240; // px per scroll

    document.getElementById('btn-left').addEventListener('click', () => {{
      track.scrollBy({{ left: -STEP * 3, behavior: 'smooth' }});
    }});
    document.getElementById('btn-right').addEventListener('click', () => {{
      track.scrollBy({{ left: STEP * 3, behavior: 'smooth' }});
    }});

    // 모바일: 버튼 숨김 (터치 스크롤 충분)
    if ('ontouchstart' in window) {{
      document.getElementById('btn-left').style.display  = 'none';
      document.getElementById('btn-right').style.display = 'none';
    }}
  </script>
</body>
</html>
"""


def main():
    preludes = collect_preludes()
    chars    = collect_characters()

    html = HTML_TEMPLATE.format(
        count         = len(preludes),
        char_count    = len(chars),
        prelude_items = build_prelude_items(preludes),
        char_items    = build_char_items(chars),
    )

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'  → {os.path.relpath(OUT_FILE, BASE_DIR)} (삽화 {len(preludes)}장, 인물 {len(chars)}명)')


if __name__ == '__main__':
    main()
