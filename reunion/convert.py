#!/usr/bin/env python3
import os
import sys
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def convert_body(text):
    def replace_tag(m):
        tag, content = m.group(1), m.group(2).strip()
        if tag == 'time':
            return f'<div class="time">{content}</div>'
        if tag == 'thought':
            return f'<p class="thought">{content}</p>'
        return content

    result = re.sub(r'<(time|thought)>([\s\S]*?)</\1>', replace_tag, text)
    result = re.sub(r'^---$', '<div class="divider">* * *</div>', result, flags=re.MULTILINE)
    result = re.sub(r'^(?!<)(.+)$', r'<p>\1</p>', result, flags=re.MULTILINE)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('사용법: python3 convert.py ep.[번호] | ep.[번호]_a', file=sys.stderr)
        sys.exit(1)

    arg = sys.argv[1]
    base_name = arg.replace('.md', '')
    input_file = os.path.join(BASE_DIR, 'episodes', f'{base_name}.md')
    output_file = os.path.join(BASE_DIR, 'html', f'{base_name}.html')

    if not os.path.exists(input_file):
        print(f'파일 없음: {input_file}', file=sys.stderr)
        sys.exit(1)

    with open(input_file, encoding='utf-8') as f:
        raw = f.read()

    ep_match = re.search(r'ep\.(\d+)(_a)?', base_name)
    ep_num = int(ep_match.group(1)) if ep_match else 0
    suffix = '_a' if '_a' in base_name else ''

    prev_link = f'<a href="ep.{ep_num - 1}{suffix}.html">← 이전 화</a>' if ep_num > 1 else '<span></span>'
    next_link = f'<a href="ep.{ep_num + 1}{suffix}.html">다음 화 →</a>'

    body = convert_body(raw)

    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>다시 만나는 관계들 — {base_name}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #1a1a1a;
      color: #e8e0d0;
      font-family: 'Nanum Myeongjo', Georgia, serif;
      font-size: 1.05rem;
      line-height: 1.95;
      max-width: 780px;
      margin: 0 auto;
      padding: 3rem 1.5rem 5rem;
    }}
    h1 {{
      font-size: 1.6rem;
      text-align: center;
      color: #c9a0b8;
      margin-bottom: 2.5rem;
      letter-spacing: 0.08em;
    }}
    p {{ margin: 0.75rem 0; }}
    .time {{
      font-weight: bold;
      color: #c9a0b8;
      font-size: 0.88rem;
      text-align: center;
      margin: 1.8rem 0 1rem;
    }}
    .thought {{ color: #9ab8c9; font-style: italic; }}
    .divider {{
      text-align: center;
      color: #444;
      margin: 2.2rem 0;
      letter-spacing: 0.6em;
    }}
    .nav {{
      display: flex;
      justify-content: space-between;
      margin-top: 3.5rem;
      padding-top: 1rem;
      border-top: 1px solid #2a2a2a;
      font-size: 0.9rem;
    }}
    .nav a {{ color: #c9a0b8; text-decoration: none; }}
    .nav a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <h1>다시 만나는 관계들 — {base_name}</h1>
  {body}
  <div class="nav">
    {prev_link}
    {next_link}
  </div>
</body>
</html>'''

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'✓ html/{base_name}.html 생성 완료')
