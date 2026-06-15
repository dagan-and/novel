#!/usr/bin/env python3
import sys, os, re

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

    if '_a' in base_name:
        print(f'건너뜀 (성인씬): {base_name}')
        continue

    adult_file = os.path.join(base_dir, 'episodes', f'{base_name}_a.md')
    if os.path.exists(adult_file):
        print(f'건너뜀 (_a 존재): {base_name}')
        continue

    if not os.path.exists(input_file):
        print(f'파일 없음: {input_file}')
        continue

    with open(input_file, 'r', encoding='utf-8') as f:
        raw = f.read()

    m = re.search(r'ep\.(\d+)(_a)?', base_name)
    ep_num = int(m.group(1)) if m else 0
    is_adult = '_a' in base_name
    suffix = '_a' if is_adult else ''

    def ep_exists(n):
        return os.path.exists(os.path.join(base_dir, 'episodes', f'ep.{n:03d}{suffix}.md'))

    prev_link = f'<a href="ep.{ep_num-1:03d}{suffix}.html">← 이전 화</a>' if ep_num > 1 and ep_exists(ep_num - 1) else '<span></span>'
    next_link = f'<a href="ep.{ep_num+1:03d}{suffix}.html">다음 화 →</a>' if ep_exists(ep_num + 1) else '<span style="color:#444">— 계속 —</span>'

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
