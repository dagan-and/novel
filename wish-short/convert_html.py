#!/usr/bin/env python3
import glob
import os
import random
import re
import sys
import unicodedata
from html import escape
from urllib.parse import quote as urlquote

from batch_paths import batch_label, html_episode_path, source_episode_path

if len(sys.argv) < 2:
    print("사용법: python3 convert_html.py ep.[번호] [ep.[번호] ...]")
    sys.exit(1)

args = sys.argv[1:]

CSS = """
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html { font-size: 120%; }
    body {
      background: #1c1a18;
      color: #bfb9b0;
      font-family: 'Pretendard', 'Noto Sans KR', 'Apple SD Gothic Neo', sans-serif;
      font-size: 1.12rem;
      line-height: 2.0;
      max-width: 760px;
      margin: 0 auto;
      padding: 3rem 1.4rem 5rem;
      word-break: keep-all;
    }
    h1 {
      font-size: 1.35rem;
      text-align: center;
      color: #6a9e98;
      margin-bottom: 2.5rem;
      letter-spacing: 0.02em;
    }
    p { margin: 0.75rem 0; }
    p.speaker-line {
      display: flex;
      align-items: baseline;
      gap: 0.7rem;
      margin: 0.68rem 0;
    }
    .speaker-tag {
      flex: 0 0 auto;
      font-size: 0.82rem;
      font-weight: 700;
      letter-spacing: 0.02em;
    }
    .speaker-text {
      flex: 1 1 auto;
    }
    .time {
      font-weight: bold;
      color: #b88a52;
      font-size: 1.08rem;
      text-align: center;
      margin: 1.8rem 0 1rem;
    }
    .thought { color: #8aaab0; font-style: italic; }
    .divider {
      text-align: center;
      color: #575450;
      margin: 2.2rem 0;
      letter-spacing: 0.6em;
    }
    figure.scene-illustration {
      margin: 2.5rem 0 2.8rem;
    }
    .scene-illustration img {
      display: block;
      width: 100%;
      border-radius: 10px;
      border: 1px solid #302e2b;
      box-shadow: 0 14px 32px rgba(0, 0, 0, 0.28);
    }
    .scene-illustration figcaption {
      margin-top: 0.8rem;
      text-align: center;
      font-size: 0.92rem;
      color: #8a918d;
      letter-spacing: 0.02em;
    }
    figure.scene-illustration-pair {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.8rem;
      margin: 2.5rem 0 2.8rem;
    }
    .scene-illustration-pair img {
      display: block;
      width: 100%;
      border-radius: 10px;
      border: 1px solid #302e2b;
      box-shadow: 0 14px 32px rgba(0, 0, 0, 0.28);
    }
    .scene-illustration-pair figcaption {
      grid-column: 1 / -1;
      margin-top: 0.5rem;
      text-align: center;
      font-size: 0.92rem;
      color: #8a918d;
      letter-spacing: 0.02em;
    }
    .nav {
      display: flex;
      justify-content: space-between;
      margin-top: 3.5rem;
      padding-top: 1rem;
      border-top: 1px solid #302e2b;
      font-size: 1rem;
    }
    .nav a { color: #7bbab3; text-decoration: none; font-weight: 700; }
    .nav a:hover { text-decoration: underline; }
"""

PRELUDE_DIR = os.path.join('images', 'preludes')
CHARACTER_IMAGE_DIR = os.path.join('images', 'characters')
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}
MALE_COLOR = '#7aa0cc'
FEMALE_COLOR = '#c07088'
EXTRA_COLOR = '#a09890'


def load_speakers(base_dir):
    char_dir = os.path.join(base_dir, 'characters')
    male, female = set(), set()
    for fname in os.listdir(char_dir):
        if not fname.endswith('.md') or fname == '캐릭터양식.md':
            continue
        name = fname[:-3]
        path = os.path.join(char_dir, fname)
        with open(path, encoding='utf-8') as f:
            content = f.read()
        if re.search(r'^- 성별:\s*남', content, re.MULTILINE):
            male.add(name)
            if len(name) > 1:
                male.add(name[1:])
        else:
            female.add(name)
            if len(name) > 1:
                female.add(name[1:])
    return male, female


def find_prelude_image(base_dir, episode_number):
    matches = []
    for name_pattern in (f'ep.{episode_number:03d}.*', f'{episode_number:03d}.*'):
        pattern = os.path.join(base_dir, PRELUDE_DIR, batch_label(episode_number), name_pattern)
        matches.extend(
            path for path in glob.glob(pattern)
            if os.path.isfile(path) and os.path.splitext(path)[1].lower() in IMAGE_EXTENSIONS
        )
    matches = sorted(set(matches))
    return matches[0] if matches else None


def find_normalized_child(parent, child_name):
    target = unicodedata.normalize('NFC', child_name)
    if not os.path.isdir(parent):
        return None
    for entry in os.listdir(parent):
        if unicodedata.normalize('NFC', entry) == target:
            return os.path.join(parent, entry)
    return None


def find_character_image(base_dir, character_name):
    images = find_character_images(base_dir, character_name, count=1)
    return images[0] if images else None


def find_character_images(base_dir, character_name, count=2):
    if not character_name:
        return []

    image_root = os.path.join(base_dir, CHARACTER_IMAGE_DIR)
    folder = find_normalized_child(image_root, character_name)
    matches = []
    if folder and os.path.isdir(folder):
        matches = sorted(
            os.path.join(folder, fname)
            for fname in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, fname))
            and os.path.splitext(fname)[1].lower() in IMAGE_EXTENSIONS
        )

    if not matches:
        for ext in IMAGE_EXTENSIONS:
            direct_path = find_normalized_child(image_root, f'{character_name}{ext}')
            if direct_path and os.path.isfile(direct_path):
                matches.append(direct_path)

    if not matches:
        return []
    return random.sample(matches, min(count, len(matches)))


def extract_adult_scene_block(text):
    pattern = re.compile(
        r'\n---\n+(##\s*(?:\[)?성인씬 #[^\n\]]+(?:\])?\n[\s\S]*?)\n---\n',
        re.MULTILINE,
    )
    match = pattern.search(text)
    return match.group(1) if match else ''


def extract_scene_characters(text, female_speakers):
    block = extract_adult_scene_block(text)
    if not block:
        return []
    full_names = sorted(
        (name for name in female_speakers if len(name) > 1),
        key=len,
        reverse=True,
    )
    found = []
    for name in full_names:
        if re.search(rf'(^|\s|[-:\[\]]){re.escape(name)}(\s|[:\]\-]|$)', block):
            found.append(name)
    return found


def _encode_image_path(abs_path, output_dir):
    rel = os.path.relpath(abs_path, output_dir).replace(os.sep, '/')
    parts = rel.split('/')
    encoded = [p if p in ('..', '.') else urlquote(unicodedata.normalize('NFC', p), safe='')
               for p in parts]
    return '/'.join(encoded)


def build_illustration_html(image_paths, episode_number, output_file, caption_text):
    if not image_paths:
        return ''
    alt = f'ep.{episode_number:03d} 성인씬 직전 상황 삽화'
    output_dir = os.path.dirname(output_file)
    if len(image_paths) == 1:
        src = _encode_image_path(image_paths[0], output_dir)
        return (
            '<figure class="scene-illustration">'
            f'<img src="{src}" alt="{alt}">'
            f'<figcaption>{caption_text}</figcaption>'
            '</figure>'
        )
    imgs_html = ''.join(
        f'<img src="{_encode_image_path(p, output_dir)}" alt="{alt}">'
        for p in image_paths
    )
    return (
        '<figure class="scene-illustration-pair">'
        + imgs_html
        + f'<figcaption>{caption_text}</figcaption>'
        '</figure>'
    )


def extract_scene_caption(text):
    match = re.search(r'^- 장소:\s*(.+)$', text, flags=re.MULTILINE)
    if match:
        return match.group(1).strip()
    return '성인씬 직전 상황 삽화'


def replace_adult_scene_block(text, illustration_html):
    pattern = re.compile(
        r'\n---\n+(?:##\s*(?:\[)?성인씬 #[^\n\]]+(?:\])?\n[\s\S]*?)\n---\n',
        re.MULTILINE,
    )
    return pattern.sub(f'\n{illustration_html}\n', text, count=1)


def find_scene_image(base_dir, episode_number, raw_text, female_speakers):
    prelude_image = find_prelude_image(base_dir, episode_number)
    if prelude_image:
        return [prelude_image]
    character_names = extract_scene_characters(raw_text, female_speakers)
    images = []
    for name in character_names:
        img = find_character_image(base_dir, name)
        if img:
            images.append(img)
    return images


def display_episode_name(base_name):
    return base_name.replace('_a', '')


def extract_display_title(text, base_name):
    for line in text.splitlines():
        match = re.match(r'^#\s+(.+?)\s*$', line)
        if match:
            return match.group(1).strip().replace('_a', '')
    return display_episode_name(base_name)


def resolve_episode_html_name(base_dir, episode_number):
    for candidate in (f'ep.{episode_number:03d}_a', f'ep.{episode_number:03d}'):
        try:
            source_episode_path(Path(base_dir), candidate)
            return candidate
        except FileNotFoundError:
            continue
    return None


def build_speaker_line(name, content, male_speakers, female_speakers):
    if name in male_speakers:
        color = MALE_COLOR
    elif name in female_speakers:
        color = FEMALE_COLOR
    else:
        color = EXTRA_COLOR
    return (
        f'<p class="speaker-line">'
        f'<span class="speaker-tag" style="color:{color}">{escape(name)}</span>'
        f'<span class="speaker-text" style="color:{color}">{escape(content)}</span>'
        f'</p>'
    )


def convert_body(text, male_speakers, female_speakers):
    # <time> 태그
    text = re.sub(r'<time>([\s\S]*?)</time>', lambda m: f'<div class="time">{m.group(1).strip()}</div>', text)
    # <thought> 태그
    text = re.sub(r'<thought>([\s\S]*?)</thought>', lambda m: f'<p class="thought">{m.group(1).strip()}</p>', text)
    # <progress> 태그 제거
    text = re.sub(r'<progress>[^<]*</progress>', '', text)
    # --- 구분선
    text = re.sub(r'^---$', '<div class="divider">* * *</div>', text, flags=re.MULTILINE)
    # # 제목 제거 (마크다운 h1, h2)
    text = re.sub(r'^#{1,2} .+$', '', text, flags=re.MULTILINE)
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
            speaker_match = re.match(r'^\[([^\]]+)\]\s*(.+)$', stripped)
            if speaker_match:
                name = speaker_match.group(1).strip()
                content = speaker_match.group(2).strip()
                result.append(build_speaker_line(name, content, male_speakers, female_speakers))
            else:
                result.append(f'<p>{escape(stripped)}</p>')
    return '\n'.join(result)

from pathlib import Path


base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
male_speakers, female_speakers = load_speakers(base_dir)

for arg in args:
    base_name = arg.replace('.md', '')
    try:
        input_file = source_episode_path(base_dir, base_name)
    except FileNotFoundError:
        print(f'파일 없음: episodes/{base_name}.md')
        continue
    output_file = html_episode_path(base_dir, base_name)

    adult_file_exists = False
    if '_a' not in base_name:
        try:
            source_episode_path(base_dir, f'{base_name}_a')
            adult_file_exists = True
        except FileNotFoundError:
            adult_file_exists = False
    if adult_file_exists:
        print(f'건너뜀 (_a 존재): {base_name}')
        continue

    with open(input_file, 'r', encoding='utf-8') as f:
        raw = f.read()

    display_title = extract_display_title(raw, base_name)
    m = re.search(r'ep\.(\d+)(_a)?', base_name)
    ep_num = int(m.group(1)) if m else 0
    scene_images = find_scene_image(base_dir, ep_num, raw, female_speakers)
    if scene_images:
        caption_text = extract_scene_caption(raw)
        raw = replace_adult_scene_block(raw, build_illustration_html(scene_images, ep_num, output_file, caption_text))
    else:
        raw = replace_adult_scene_block(raw, '')

    prev_name = resolve_episode_html_name(base_dir, ep_num - 1) if ep_num > 1 else None
    next_name = resolve_episode_html_name(base_dir, ep_num + 1)

    if prev_name:
        prev_target = html_episode_path(base_dir, prev_name)
        prev_href = os.path.relpath(prev_target, output_file.parent).replace(os.sep, '/')
        prev_link = f'<a href="{prev_href}">← 이전 화</a>'
    else:
        prev_link = '<span></span>'
    if next_name:
        next_target = html_episode_path(base_dir, next_name)
        next_href = os.path.relpath(next_target, output_file.parent).replace(os.sep, '/')
        next_link = f'<a href="{next_href}">다음 화 →</a>'
    else:
        next_link = '<span style="color:#444">— 계속 —</span>'

    body = convert_body(raw, male_speakers, female_speakers)

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{display_title}</title>
  <style>{CSS}  </style>
</head>
<body>
  <h1>{display_title}</h1>
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
    print(f'✓ html/{output_file.relative_to(base_dir / "html").as_posix()} 생성 완료')
