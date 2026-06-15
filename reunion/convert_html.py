#!/usr/bin/env python3
import glob
import os
import re
import sys

if len(sys.argv) < 2:
    print("사용법: python3 convert_html.py ep.[번호] [ep.[번호] ...]")
    sys.exit(1)

args = sys.argv[1:]

CSS = """
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #232120;
      color: #a8a09a;
      font-family: 'Nanum Myeongjo', Georgia, serif;
      font-size: 1.38rem;
      line-height: 1.9;
      max-width: 780px;
      margin: 0 auto;
      padding: 3rem 1.5rem 5rem;
    }
    h1 {
      font-size: 1.44rem;
      text-align: center;
      color: #b890a8;
      margin-bottom: 2.5rem;
      letter-spacing: 0.08em;
    }
    p { margin: 0.75rem 0; }
    .time {
      font-weight: bold;
      color: #b890a8;
      font-size: 1.25rem;
      text-align: center;
      margin: 1.8rem 0 1rem;
    }
    .thought { color: #7aa0b0; font-style: italic; }
    .divider {
      text-align: center;
      color: #484240;
      margin: 2.2rem 0;
      letter-spacing: 0.6em;
    }
    figure.scene-illustration {
      margin: 2.5rem 0 2.8rem;
    }
    .scene-illustration img {
      display: block;
      width: 100%;
      border-radius: 16px;
      border: 1px solid #3a3431;
      box-shadow: 0 18px 40px rgba(0, 0, 0, 0.24);
    }
    .scene-illustration figcaption {
      margin-top: 0.8rem;
      text-align: center;
      font-size: 1.02rem;
      color: #8e8179;
      letter-spacing: 0.04em;
    }
    .nav {
      display: flex;
      justify-content: space-between;
      margin-top: 3.5rem;
      padding-top: 1rem;
      border-top: 1px solid #302c2a;
      font-size: 1.19rem;
    }
    .nav a { color: #b890a8; text-decoration: none; }
    .nav a:hover { text-decoration: underline; }
"""

PRELUDE_DIR = os.path.join('images', 'preludes')


def find_prelude_image(base_dir, episode_number):
    matches = []
    for name_pattern in (f'ep.{episode_number:03d}.*', f'{episode_number:03d}.*'):
        pattern = os.path.join(base_dir, PRELUDE_DIR, name_pattern)
        matches.extend(
            path for path in glob.glob(pattern)
            if os.path.isfile(path) and os.path.splitext(path)[1].lower() in {'.png', '.jpg', '.jpeg', '.webp', '.gif'}
        )
    matches = sorted(set(matches))
    return matches[0] if matches else None


def build_illustration_html(image_path, episode_number, output_file, caption_text):
    rel_path = os.path.relpath(image_path, os.path.dirname(output_file)).replace(os.sep, '/')
    return (
        '<figure class="scene-illustration">'
        f'<img src="{rel_path}" alt="ep.{episode_number:03d} 성인씬 직전 상황 삽화">'
        f'<figcaption>{caption_text}</figcaption>'
        '</figure>'
    )


def extract_scene_caption(text):
    match = re.search(r'^- 장소:\s*(.+)$', text, flags=re.MULTILINE)
    if match:
        return match.group(1).strip()
    return '성인씬 직전 상황 삽화'


def replace_adult_scene_block(text, illustration_html):
    pattern = re.compile(
        r'\n---\n## \[성인씬 #[^\n]+\]\n[\s\S]*?\n---\n',
        re.MULTILINE,
    )
    return pattern.sub(f'\n{illustration_html}\n', text, count=1)


def resolve_episode_html_name(base_dir, episode_number):
    for candidate in (f'ep.{episode_number:03d}_a', f'ep.{episode_number:03d}'):
        if os.path.exists(os.path.join(base_dir, 'episodes', f'{candidate}.md')):
            return candidate
    return None

def convert_body(text):
    # <time> 태그
    text = re.sub(r'<time>([\s\S]*?)</time>', lambda m: f'<div class="time">{m.group(1).strip()}</div>', text)
    # <thought> 태그
    text = re.sub(r'<thought>([\s\S]*?)</thought>', lambda m: f'<p class="thought">{m.group(1).strip()}</p>', text)
    # --- 구분선
    text = re.sub(r'^---$', '<div class="divider">* * *</div>', text, flags=re.MULTILINE)
    # # 제목 제거 (마크다운 h1)
    text = re.sub(r'^# .+$', '', text, flags=re.MULTILINE)
    # 일반 텍스트 줄 → <p>
    lines = text.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            result.append('')
        elif stripped.startswith('<'):
            result.append(stripped)
        else:
            result.append(f'<p>{stripped}</p>')
    return '\n'.join(result)

base_dir = os.path.dirname(os.path.abspath(__file__))

for arg in args:
    base_name = arg.replace('.md', '')
    input_file = os.path.join(base_dir, 'episodes', f'{base_name}.md')
    output_file = os.path.join(base_dir, 'html', f'{base_name}.html')

    adult_file = os.path.join(base_dir, 'episodes', f'{base_name}_a.md')
    if '_a' not in base_name and os.path.exists(adult_file):
        print(f'건너뜀 (_a 존재): {base_name}')
        continue

    if not os.path.exists(input_file):
        print(f'파일 없음: {input_file}')
        continue

    with open(input_file, 'r', encoding='utf-8') as f:
        raw = f.read()

    m = re.search(r'ep\.(\d+)(_a)?', base_name)
    ep_num = int(m.group(1)) if m else 0
    prelude_image = find_prelude_image(base_dir, ep_num)
    if '_a' in base_name and prelude_image:
        caption_text = extract_scene_caption(raw)
        raw = replace_adult_scene_block(raw, build_illustration_html(prelude_image, ep_num, output_file, caption_text))

    prev_name = resolve_episode_html_name(base_dir, ep_num - 1) if ep_num > 1 else None
    next_name = resolve_episode_html_name(base_dir, ep_num + 1)

    prev_link = f'<a href="{prev_name}.html">← 이전 화</a>' if prev_name else '<span></span>'
    next_link = f'<a href="{next_name}.html">다음 화 →</a>' if next_name else '<span style="color:#444">— 계속 —</span>'

    body = convert_body(raw)

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>다시 만나는 관계들 — {base_name}</title>
  <style>{CSS}  </style>
</head>
<body>
  <h1>다시 만나는 관계들 — {base_name}</h1>
  {body}
  <div class="nav">
    {prev_link}
    {next_link}
  </div>
</body>
</html>"""

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'✓ html/{base_name}.html 생성 완료')
