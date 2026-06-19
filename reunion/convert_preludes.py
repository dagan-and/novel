#!/usr/bin/env python3
"""
convert_preludes.py — preludes.html 생성
  - 상단: 최신화부터 세로 스크롤로 내려보는 대형 삽화 갤러리
"""

import os, re, unicodedata
from pathlib import Path

def nfc(s):
    return unicodedata.normalize('NFC', s)

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
IMG_PRE   = os.path.join(BASE_DIR, 'images', 'preludes')
OUT_FILE  = os.path.join(BASE_DIR, 'html', 'preludes.html')


def collect_preludes():
    """images/preludes/ 에서 NNN.png 목록 수집 → 최신화부터 정렬"""
    items = []
    for path in sorted(Path(IMG_PRE).rglob('*.png')):
        m = re.match(r'^ep\.(\d+)(?:_a)?\.png$|^(\d+)\.png$', path.name)
        if m:
            ep_num = int(m.group(1) or m.group(2))
            rel_path = os.path.relpath(path, os.path.dirname(OUT_FILE)).replace(os.sep, '/')
            items.append((ep_num, rel_path))
    return sorted(items, reverse=True)


def build_prelude_items(preludes):
    lines = []
    for ep_num, rel_path in preludes:
        ep_id  = f'ep.{ep_num:03d}'
        lines.append(
            f'      <div class="prelude-item">\n'
            f'        <img src="{rel_path}" alt="{ep_id} 삽화" loading="lazy">\n'
            f'        <span>{ep_id}</span>\n'
            f'      </div>'
        )
    return '\n'.join(lines)


HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>삽화</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #1a1a1a;
      color: #e8e0d0;
      font-family: 'Nanum Myeongjo', Georgia, serif;
      max-width: 1180px;
      margin: 0 auto;
      padding: 2.5rem 1.5rem 5rem;
    }}
    a.back {{
      display: inline-block; margin-bottom: 2.5rem;
      color: #c9a0b8; text-decoration: none; font-size: 1.05rem;
    }}
    a.back:hover {{ text-decoration: underline; }}
    /* ── 삽화 세로 스크롤 영역 ── */
    .gallery-wrap {{
      position: relative;
      margin-bottom: 3.5rem;
    }}
    .gallery-track {{
      display: flex;
      flex-direction: column;
      gap: 2.5rem;
      overflow-y: auto;
      max-height: calc(100vh - 220px);
      scroll-snap-type: y proximity;
      -webkit-overflow-scrolling: touch;
      padding: 0.25rem 0.5rem 1rem 0;
      scrollbar-width: thin;
      scrollbar-color: #3a2030 #1a1a1a;
    }}
    .gallery-track::-webkit-scrollbar {{ width: 8px; }}
    .gallery-track::-webkit-scrollbar-track {{ background: #1a1a1a; }}
    .gallery-track::-webkit-scrollbar-thumb {{ background: #3a2030; border-radius: 3px; }}

    .prelude-item {{
      scroll-snap-align: start;
      display: flex; flex-direction: column; align-items: center;
      text-decoration: none; color: #e8e0d0;
      width: 100%;
    }}
    .prelude-item img {{
      width: min(100%, 780px);
      height: auto;
      border: 1px solid #3a2030; border-radius: 3px;
      background: #111;
      transition: border-color 0.2s;
      box-shadow: 0 14px 40px rgba(0,0,0,0.28);
    }}
    .prelude-item:hover img {{ border-color: #c9a0b8; }}
    .prelude-item span {{
      margin-top: 0.75rem; font-size: 1.05rem; color: #9a8c94;
      letter-spacing: 0.08em;
    }}
    .prelude-item:hover span {{ color: #c9a0b8; }}

  </style>
</head>
<body>

  <a class="back" href="index.html">← 목차</a>

  <div class="gallery-wrap">
    <div class="gallery-track" id="gallery-track">
{prelude_items}
    </div>
  </div>

</body>
</html>
"""


def main():
    preludes = collect_preludes()

    html = HTML_TEMPLATE.format(
        count         = len(preludes),
        prelude_items = build_prelude_items(preludes),
    )

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'  → {os.path.relpath(OUT_FILE, BASE_DIR)} (삽화 {len(preludes)}장)')


if __name__ == '__main__':
    main()
