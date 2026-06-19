#!/usr/bin/env python3
"""
convert_preludes.py — preludes.html 생성
  - 상단: 100화 단위 버튼
  - 본문: 선택한 구간 삽화를 스크롤 한 번에 한 장씩 넘기는 갤러리
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
    if not Path(IMG_PRE).is_dir():
        return []
    items = []
    for path in sorted(Path(IMG_PRE).rglob('*.png')):
        m = re.match(r'^ep\.(\d+)(?:_a)?\.png$|^(\d+)\.png$', path.name)
        if m:
            ep_num = int(m.group(1) or m.group(2))
            rel_path = os.path.relpath(path, os.path.dirname(OUT_FILE)).replace(os.sep, '/')
            items.append((ep_num, rel_path))
    return sorted(items, reverse=True)


def collect_ranges(preludes):
    ranges = {}
    if Path(IMG_PRE).is_dir():
        for child in sorted(Path(IMG_PRE).iterdir()):
            if child.is_dir() and re.match(r'^\d{3}-\d{3}$', child.name):
                ranges.setdefault(child.name, [])

    for ep_num, rel_path in preludes:
        start = ((ep_num - 1) // 100) * 100 + 1
        end = start + 99
        range_id = f'{start:03d}-{end:03d}'
        ranges.setdefault(range_id, []).append((ep_num, rel_path))

    for range_id in ranges:
        ranges[range_id] = sorted(ranges[range_id], reverse=True)
    return dict(sorted(ranges.items()))


def active_range_id(ranges):
    for range_id in sorted(ranges.keys(), reverse=True):
        if ranges[range_id]:
            return range_id
    return next(iter(ranges), '001-100')


def build_range_tabs(ranges, active_id):
    lines = []
    for range_id in sorted(ranges.keys()):
        active = ' active' if range_id == active_id else ''
        selected = 'true' if range_id == active_id else 'false'
        count = len(ranges[range_id])
        lines.append(
            f'    <button class="range-tab{active}" type="button" '
            f'data-range-target="{range_id}" aria-selected="{selected}">'
            f'{range_id}<span>{count}</span></button>'
        )
    return '\n'.join(lines)


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


def build_range_panels(ranges, active_id):
    panels = []
    for range_id in sorted(ranges.keys()):
        active = ' active' if range_id == active_id else ''
        items = build_prelude_items(ranges[range_id])
        if not items:
            items = (
                f'      <div class="empty-state">\n'
                f'        <strong>{range_id}</strong>\n'
                f'        <span>삽화 없음</span>\n'
                f'      </div>'
            )
        panels.append(
            f'    <section class="range-panel{active}" data-range-panel="{range_id}">\n'
            f'      <div class="gallery-track" data-gallery-track>\n'
            f'{items}\n'
            f'      </div>\n'
            f'    </section>'
        )
    return '\n'.join(panels)


HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>삽화</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html {{ font-size: 120%; }}
    body {{
      background: #111417;
      color: #e8e1d5;
      font-family: 'Pretendard', 'Noto Sans KR', 'Apple SD Gothic Neo', sans-serif;
      min-height: 100vh;
      margin: 0 auto;
      padding: 1rem 1.2rem 1.2rem;
      overflow: hidden;
    }}
    a.back {{
      display: inline-block; margin-bottom: 0.9rem;
      color: #8fd0c9; text-decoration: none; font-size: 1rem; font-weight: 700;
    }}
    a.back:hover {{ text-decoration: underline; }}
    .range-tabs {{
      display: flex;
      gap: 0.45rem;
      margin-bottom: 0.8rem;
      overflow-x: auto;
      padding-bottom: 0.2rem;
    }}
    .range-tab {{
      border: 1px solid #30383a;
      border-radius: 8px;
      background: #181d20;
      color: #c7d0cc;
      cursor: pointer;
      font: inherit;
      font-size: 0.9rem;
      font-weight: 800;
      padding: 0.45rem 0.7rem;
      white-space: nowrap;
    }}
    .range-tab span {{
      color: #8f9996;
      font-size: 0.75rem;
      margin-left: 0.35rem;
    }}
    .range-tab.active {{
      border-color: #79b8b2;
      color: #dff7f1;
      background: #203032;
    }}
    .gallery-wrap {{
      position: relative;
      height: calc(100vh - 6.3rem);
      min-height: 420px;
    }}
    .range-panel {{
      display: none;
      height: 100%;
    }}
    .range-panel.active {{
      display: block;
    }}
    .gallery-track {{
      display: flex;
      flex-direction: column;
      gap: 0;
      overflow-y: auto;
      height: 100%;
      scroll-snap-type: y mandatory;
      -webkit-overflow-scrolling: touch;
      overscroll-behavior: contain;
      scrollbar-width: thin;
      scrollbar-color: #4f6667 #111417;
    }}
    .gallery-track::-webkit-scrollbar {{ width: 8px; }}
    .gallery-track::-webkit-scrollbar-track {{ background: #111417; }}
    .gallery-track::-webkit-scrollbar-thumb {{ background: #4f6667; border-radius: 3px; }}

    .prelude-item {{
      scroll-snap-align: start;
      scroll-snap-stop: always;
      min-height: 100%;
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      text-decoration: none; color: #e8e1d5;
      width: 100%;
      padding: 0.25rem 0 0.8rem;
    }}
    .prelude-item img {{
      width: min(100%, 980px);
      max-height: calc(100vh - 10rem);
      height: auto;
      object-fit: contain;
      border: 1px solid #30383a; border-radius: 8px;
      background: #181d20;
      transition: border-color 0.2s;
      box-shadow: 0 14px 40px rgba(0,0,0,0.28);
    }}
    .prelude-item:hover img {{ border-color: #79b8b2; }}
    .prelude-item span {{
      margin-top: 0.75rem; font-size: 1rem; color: #9faaa6;
      letter-spacing: 0.03em;
    }}
    .prelude-item:hover span {{ color: #8fd0c9; }}
    .empty-state {{
      height: 100%;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 0.35rem;
      color: #8f9996;
      border: 1px solid #30383a;
      border-radius: 8px;
      background: #181d20;
    }}
    .empty-state strong {{ color: #dff7f1; }}
    @media (max-width: 640px) {{
      body {{ padding: 0.75rem 0.65rem; }}
      .gallery-wrap {{ height: calc(100vh - 5.4rem); min-height: 360px; }}
      .range-tab {{ font-size: 0.78rem; padding: 0.38rem 0.55rem; }}
      .prelude-item span {{ font-size: 0.86rem; }}
      .prelude-item img {{ max-height: calc(100vh - 8.6rem); }}
    }}

  </style>
</head>
<body>

  <a class="back" href="index.html">← 목차</a>
  <div class="range-tabs" role="tablist" aria-label="삽화 구간">
{range_tabs}
  </div>

  <div class="gallery-wrap">
{range_panels}
  </div>
  <script>
    const tabs = Array.from(document.querySelectorAll('[data-range-target]'));
    const panels = Array.from(document.querySelectorAll('[data-range-panel]'));

    function activeTrack() {{
      return document.querySelector('.range-panel.active [data-gallery-track]');
    }}

    function itemIndex(track) {{
      const items = Array.from(track.querySelectorAll('.prelude-item'));
      if (!items.length) return 0;
      const top = track.scrollTop;
      let bestIndex = 0;
      let bestDistance = Infinity;
      items.forEach((item, index) => {{
        const distance = Math.abs(item.offsetTop - top);
        if (distance < bestDistance) {{
          bestDistance = distance;
          bestIndex = index;
        }}
      }});
      return bestIndex;
    }}

    function scrollToItem(track, index) {{
      const items = Array.from(track.querySelectorAll('.prelude-item'));
      if (!items.length) return;
      const safeIndex = Math.max(0, Math.min(index, items.length - 1));
      track.scrollTo({{ top: items[safeIndex].offsetTop, behavior: 'smooth' }});
    }}

    function showRange(rangeId) {{
      tabs.forEach((tab) => {{
        const active = tab.dataset.rangeTarget === rangeId;
        tab.classList.toggle('active', active);
        tab.setAttribute('aria-selected', String(active));
      }});
      panels.forEach((panel) => {{
        const active = panel.dataset.rangePanel === rangeId;
        panel.classList.toggle('active', active);
        if (active) {{
          const track = panel.querySelector('[data-gallery-track]');
          if (track) track.scrollTop = 0;
        }}
      }});
    }}

    tabs.forEach((tab) => {{
      tab.addEventListener('click', () => showRange(tab.dataset.rangeTarget));
    }});

    document.querySelectorAll('[data-gallery-track]').forEach((track) => {{
      let wheelLocked = false;
      track.addEventListener('wheel', (event) => {{
        const items = track.querySelectorAll('.prelude-item');
        if (!items.length) return;
        event.preventDefault();
        if (wheelLocked) return;
        wheelLocked = true;
        const direction = event.deltaY > 0 ? 1 : -1;
        const nextIndex = itemIndex(track) + direction;
        scrollToItem(track, nextIndex);
        window.setTimeout(() => {{ wheelLocked = false; }}, 420);
      }}, {{ passive: false }});
    }});

    document.addEventListener('keydown', (event) => {{
      const track = activeTrack();
      if (!track) return;
      if (event.key === 'ArrowDown' || event.key === 'ArrowRight') {{
        event.preventDefault();
        scrollToItem(track, itemIndex(track) + 1);
      }}
      if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') {{
        event.preventDefault();
        scrollToItem(track, itemIndex(track) - 1);
      }}
    }});
  </script>

</body>
</html>
"""


def main():
    preludes = collect_preludes()
    ranges = collect_ranges(preludes)
    active_id = active_range_id(ranges)

    html = HTML_TEMPLATE.format(
        count         = len(preludes),
        range_tabs    = build_range_tabs(ranges, active_id),
        range_panels  = build_range_panels(ranges, active_id),
    )

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'  → {os.path.relpath(OUT_FILE, BASE_DIR)} (삽화 {len(preludes)}장)')


if __name__ == '__main__':
    main()
