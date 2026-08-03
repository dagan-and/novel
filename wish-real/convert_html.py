#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EPISODES_DIR = ROOT / "episodes"
HTML_DIR = ROOT / "html"
CHARACTERS_DIR = ROOT / "characters"
CHARACTER_ASSETS_DIR = ROOT / "character_assets"

EP_PATTERN = re.compile(r"^ep\.(\d+)(?P<suffix>_a|\.sample)?\.md$")
DIALOGUE_PATTERN = re.compile(r'^\[(?P<speaker>.+?)\]\s+"(?P<line>.*)"$')
MESSAGE_PATTERN = re.compile(r"^\[(?P<sender>.+?)\]\s+(?P<body>.+)$")
IMAGE_PATTERN = re.compile(r"^!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]+)\)$")
CHARACTER_EXCLUDES = {"캐릭터양식"}


def batch_label(ep_num: int) -> str:
    start = ((ep_num - 1) // 100) * 100 + 1
    return f"{start:03d}-{start + 99:03d}"


def episode_path(ep_num: int) -> Path:
    return EPISODES_DIR / batch_label(ep_num) / f"ep.{ep_num:03d}.md"


def output_path(ep_num: int, suffix: str = "") -> Path:
    return HTML_DIR / batch_label(ep_num) / f"ep.{ep_num:03d}{suffix}.html"


def output_path_for_source(source: Path) -> Path:
    matched = EP_PATTERN.match(source.name)
    if not matched:
        raise ValueError(f"Episode filename must look like ep.001.md: {source}")
    ep_num = int(matched.group(1))
    suffix = matched.group("suffix") or ""
    return output_path(ep_num, suffix)


def relative_nav_href(from_ep: int, to_ep: int) -> str:
    from_dir = HTML_DIR / batch_label(from_ep)
    target = output_path(to_ep)
    return target.relative_to(from_dir) if target.parent == from_dir else f"../{batch_label(to_ep)}/{target.name}"


def nav_item(label: str, href: str | None) -> str:
    if href is None:
        return f'<span class="nav-link disabled">{html.escape(label)}</span>'
    return f'<a class="nav-link" href="{html.escape(href)}">{html.escape(label)}</a>'


def render_navigation(ep_num: int) -> str:
    prev_ep = ep_num - 1 if episode_path(ep_num - 1).exists() else None
    next_ep = ep_num + 1 if episode_path(ep_num + 1).exists() else None
    prev_href = str(relative_nav_href(ep_num, prev_ep)) if prev_ep else None
    next_href = str(relative_nav_href(ep_num, next_ep)) if next_ep else None
    return (
        '<nav class="episode-nav" aria-label="Episode navigation">'
        f"{nav_item('이전화', prev_href)}"
        f'{nav_item("목록", "../index.html")}'
        f"{nav_item('다음화', next_href)}"
        "</nav>"
    )


def split_blocks(text: str) -> list[list[str]]:
    lines = text.splitlines()
    blocks: list[list[str]] = []
    current: list[str] = []

    for raw_line in lines:
        line = raw_line.rstrip()
        if not line:
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(line)

    if current:
        blocks.append(current)
    return blocks


def render_inline_text(value: str) -> str:
    return html.escape(value)


def render_profile_inline(value: str) -> str:
    escaped = html.escape(value)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
    return escaped


def render_single_line_block(line: str) -> str:
    if line.startswith("# "):
        return f"<h1>{render_inline_text(line[2:])}</h1>"

    if line.startswith("## "):
        return f"<h2>{render_inline_text(line[3:])}</h2>"

    if line.startswith("> "):
        return f"<blockquote>{render_inline_text(line[2:])}</blockquote>"

    if line == "---":
        return '<div class="divider">* * *</div>'

    image = IMAGE_PATTERN.match(line)
    if image:
        alt = html.escape(image.group("alt"), quote=True)
        src = html.escape(image.group("src"), quote=True)
        return f'<figure class="episode-image"><img src="{src}" alt="{alt}" loading="lazy"></figure>'

    dialogue = DIALOGUE_PATTERN.match(line)
    if dialogue:
        speaker = html.escape(dialogue.group("speaker"))
        body = html.escape(dialogue.group("line"))
        return (
            '<p class="dialogue">'
            f'<span class="speaker">[{speaker}]</span> '
            f'<span class="line">"{body}"</span>'
            "</p>"
        )

    message = MESSAGE_PATTERN.match(line)
    if message:
        sender = html.escape(message.group("sender"))
        body = html.escape(message.group("body"))
        return (
            '<p class="message">'
            f'<span class="message-sender">[{sender}]</span> '
            f'<span class="message-body">{body}</span>'
            "</p>"
        )

    return f"<p>{render_inline_text(line)}</p>"


def render_block(block: list[str]) -> str:
    if not block:
        return ""
    if len(block) == 1:
        return render_single_line_block(block[0])

    escaped = "<br>\n".join(render_inline_text(line) for line in block)
    return f"<p>{escaped}</p>"


def render_profile_markdown(text: str) -> str:
    lines = re.sub(r"^# .+\n?", "", text).splitlines()
    rendered: list[str] = []
    in_list = False

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            rendered.append("</ul>")
            in_list = False

    for raw_line in lines:
        line = raw_line.rstrip()
        if line.startswith("- "):
            if not in_list:
                rendered.append("<ul>")
                in_list = True
            rendered.append(f"<li>{render_profile_inline(line[2:])}</li>")
            continue

        close_list()
        if not line:
            continue
        if line.startswith("### "):
            rendered.append(f"<h3>{render_profile_inline(line[4:])}</h3>")
        elif line.startswith("## "):
            rendered.append(f"<h2>{render_profile_inline(line[3:])}</h2>")
        elif line == "---":
            rendered.append("<hr>")
        else:
            rendered.append(f"<p>{render_profile_inline(line)}</p>")

    close_list()
    return "\n".join(rendered)


def page_title(ep_num: int) -> str:
    return f"wish-real ep.{ep_num:03d}"


def render_episode(text: str, ep_num: int) -> str:
    rendered = "\n".join(render_block(block) for block in split_blocks(text) if block)
    nav = render_navigation(ep_num)
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{page_title(ep_num)}</title>
  <style>
    :root {{
      color-scheme: dark light;
      --bg: #171717;
      --panel: #22201f;
      --text: #ece5dc;
      --muted: #afa69d;
      --accent: #d7a36c;
      --line: #473f39;
      --message-bg: rgba(215, 163, 108, 0.12);
    }}
    @media (prefers-color-scheme: light) {{
      :root {{
        --bg: #eee8df;
        --panel: #fbf7f0;
        --text: #2f2924;
        --muted: #74695f;
        --accent: #8b5d34;
        --line: #d4c5b7;
        --message-bg: rgba(139, 93, 52, 0.1);
      }}
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: "Apple SD Gothic Neo", "Noto Sans KR", system-ui, sans-serif;
      line-height: 1.85;
    }}
    main {{
      max-width: 800px;
      min-height: 100vh;
      margin: 0 auto;
      padding: 48px 20px 80px;
      background: var(--panel);
    }}
    h1, h2 {{
      line-height: 1.35;
      letter-spacing: 0;
    }}
    h1 {{
      margin: 0 0 2rem;
      font-size: 2.38rem;
    }}
    h2 {{
      margin: 2rem 0 1rem;
      font-size: 1.69rem;
    }}
    p, blockquote {{
      margin: 0 0 1rem;
      font-size: 1.33rem;
    }}
    blockquote {{
      padding-left: 1rem;
      border-left: 3px solid var(--line);
      color: var(--muted);
    }}
    .dialogue .speaker {{
      color: var(--accent);
      font-weight: 800;
    }}
    .message {{
      padding: 0.75rem 0.85rem;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--message-bg);
      color: var(--text);
    }}
    .message-sender {{
      color: var(--accent);
      font-weight: 800;
    }}
    .episode-image {{
      margin: 1.8rem 0 2rem;
    }}
    .episode-image img {{
      display: block;
      width: 100%;
      height: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #111;
    }}
    .divider {{
      margin: 2rem 0;
      text-align: center;
      color: var(--muted);
      letter-spacing: 0.35rem;
    }}
    .episode-nav {{
      display: flex;
      gap: 12px;
      justify-content: center;
      margin-top: 3rem;
      flex-wrap: wrap;
    }}
    .nav-link {{
      min-width: 104px;
      padding: 10px 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      color: var(--text);
      text-align: center;
      text-decoration: none;
    }}
    .nav-link.disabled {{
      color: var(--muted);
      opacity: 0.5;
    }}
  </style>
</head>
<body>
  <main>
{rendered}
{nav}
  </main>
</body>
</html>
"""


CHARACTER_INDEX_CSS = """
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: #171717;
      color: #ece5dc;
      font-family: "Apple SD Gothic Neo", "Noto Sans KR", system-ui, sans-serif;
      word-break: keep-all;
    }
    main {
      max-width: 980px;
      min-height: 100vh;
      margin: 0 auto;
      padding: 28px 16px 56px;
    }
    .top-link {
      display: inline-block;
      margin-bottom: 18px;
      color: #d7a36c;
      font-weight: 800;
      text-decoration: none;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
      gap: 12px;
    }
    .card {
      position: relative;
      display: flex;
      min-height: 260px;
      align-items: flex-end;
      overflow: hidden;
      border: 1px solid #473f39;
      border-radius: 8px;
      background: #22201f;
      color: #ece5dc;
      text-decoration: none;
      box-shadow: 0 14px 34px rgba(0, 0, 0, 0.24);
    }
    .card::after {
      content: "";
      position: absolute;
      inset: 0;
      background: linear-gradient(180deg, rgba(23,23,23,0) 30%, rgba(23,23,23,0.9) 100%);
    }
    .card img, .no-image {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      object-position: top;
      transition: transform 0.2s ease, filter 0.2s ease;
    }
    .no-image {
      display: flex;
      align-items: center;
      justify-content: center;
      color: #afa69d;
      font-size: 3.75rem;
      background: #22201f;
    }
    .card:hover img {
      transform: scale(1.035);
      filter: brightness(1.08);
    }
    .card-text {
      position: relative;
      z-index: 1;
      width: 100%;
      padding: 16px;
      text-shadow: 0 1px 8px rgba(0, 0, 0, 0.9);
    }
    .card strong {
      display: block;
      font-size: 1.45rem;
      line-height: 1.25;
    }
    .card span {
      display: block;
      margin-top: 4px;
      color: #d7a36c;
      font-size: 1.1rem;
      font-weight: 800;
    }
    @media (max-width: 560px) {
      main { padding: 16px 10px 44px; }
      .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
      .card { min-height: 210px; }
      .card-text { padding: 12px; }
    }
"""


CHARACTER_PROFILE_CSS = """
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: #171717;
      color: #ece5dc;
      font-family: "Apple SD Gothic Neo", "Noto Sans KR", system-ui, sans-serif;
      line-height: 1.82;
      word-break: keep-all;
    }
    main {
      max-width: 840px;
      min-height: 100vh;
      margin: 0 auto;
      padding: 34px 18px 72px;
      background: #22201f;
    }
    .back {
      display: inline-block;
      margin-bottom: 24px;
      color: #d7a36c;
      font-weight: 800;
      text-decoration: none;
    }
    .header {
      display: grid;
      gap: 22px;
      margin-bottom: 32px;
      padding-bottom: 28px;
      border-bottom: 1px solid #473f39;
    }
    .portrait {
      overflow: hidden;
      border: 1px solid #473f39;
      border-radius: 8px;
      background: #171717;
    }
    .portrait img {
      display: block;
      width: 100%;
      max-height: 72vh;
      object-fit: contain;
      object-position: top;
      cursor: zoom-in;
    }
    .portrait.no-image {
      min-height: 220px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #afa69d;
      font-size: 2.5rem;
    }
    h1 {
      margin: 0;
      color: #d7a36c;
      font-size: 3rem;
      line-height: 1.25;
      letter-spacing: 0;
      text-align: center;
    }
    h2 {
      margin: 2rem 0 0.7rem;
      padding-bottom: 0.35rem;
      border-bottom: 1px solid #473f39;
      color: #d7a36c;
      font-size: 1.56rem;
      letter-spacing: 0;
    }
    h3 {
      margin: 1.25rem 0 0.45rem;
      color: #e1b98d;
      font-size: 1.35rem;
      letter-spacing: 0;
    }
    p, ul {
      margin: 0 0 0.85rem;
      font-size: 1.3rem;
    }
    ul { padding-left: 1.3rem; }
    li { margin: 0.28rem 0; }
    hr {
      margin: 1.8rem 0;
      border: 0;
      border-top: 1px solid #473f39;
    }
    strong { color: #e1b98d; }
    code {
      padding: 0.08rem 0.3rem;
      border-radius: 4px;
      background: rgba(215, 163, 108, 0.12);
      color: #e1b98d;
    }
    #lightbox {
      display: none;
      position: fixed;
      inset: 0;
      z-index: 10;
      align-items: center;
      justify-content: center;
      background: rgba(0, 0, 0, 0.9);
      cursor: zoom-out;
    }
    #lightbox.open { display: flex; }
    #lightbox img {
      max-width: 92vw;
      max-height: 92vh;
      border: 1px solid #473f39;
      border-radius: 8px;
      object-fit: contain;
    }
"""


INDEX_CSS = """
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: #171717;
      color: #ece5dc;
      font-family: "Apple SD Gothic Neo", "Noto Sans KR", system-ui, sans-serif;
      word-break: keep-all;
    }
    main {
      max-width: 920px;
      min-height: 100vh;
      margin: 0 auto;
      padding: 34px 18px 72px;
    }
    .subtitle {
      margin: 0 0 22px;
      color: #afa69d;
      text-align: center;
      font-weight: 800;
    }
    .layout {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 170px;
      gap: 18px;
      align-items: start;
    }
    .batch {
      margin-bottom: 14px;
      padding: 16px;
      border: 1px solid #473f39;
      border-radius: 8px;
      background: #22201f;
    }
    .batch h2 {
      margin: 0 0 12px;
      color: #d7a36c;
      font-size: 1.25rem;
      letter-spacing: 0;
    }
    .episode-links {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .episode-links a, .utility a {
      border: 1px solid #473f39;
      border-radius: 8px;
      color: #ece5dc;
      text-decoration: none;
      background: rgba(215, 163, 108, 0.08);
    }
    .episode-links a {
      min-width: 42px;
      padding: 8px 10px;
      text-align: center;
      font-weight: 800;
    }
    .utility {
      display: grid;
      gap: 10px;
    }
    .utility a {
      padding: 12px 14px;
      color: #d7a36c;
      font-weight: 900;
      text-align: center;
    }
    a:hover {
      border-color: #d7a36c;
      text-decoration: underline;
    }
    @media (max-width: 700px) {
      main { padding: 20px 10px 54px; }
      .layout { grid-template-columns: 1fr; }
      .utility { order: -1; grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
"""


def render_site_index(episode_files: list[Path]) -> str:
    episodes: list[tuple[int, Path]] = []
    for source in episode_files:
        matched = EP_PATTERN.match(source.name)
        if matched and matched.group("suffix") != ".sample":
            episodes.append((int(matched.group(1)), output_path_for_source(source)))

    batches: dict[str, list[tuple[int, Path]]] = {}
    for ep_num, dest in sorted(episodes):
        batches.setdefault(batch_label(ep_num), []).append((ep_num, dest))

    batch_blocks = []
    for label, items in batches.items():
        links = "\n          ".join(
            f'<a href="{html.escape(str(dest.relative_to(HTML_DIR)), quote=True)}">{ep_num}</a>'
            for ep_num, dest in items
        )
        batch_blocks.append(
            '<section class="batch">'
            f"<h2>{html.escape(label)}</h2>"
            f'<div class="episode-links">{links}</div>'
            "</section>"
        )
    episode_total = len(episodes)
    content = "\n      ".join(batch_blocks) if batch_blocks else "<p>생성된 에피소드가 없습니다.</p>"
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>wish-real 목차</title>
  <style>{INDEX_CSS}  </style>
</head>
<body>
  <main>
    <p class="subtitle">총 {episode_total}화</p>
    <div class="layout">
      <div>
      {content}
      </div>
      <nav class="utility" aria-label="바로가기">
        <a href="characters.html">인물</a>
      </nav>
    </div>
  </main>
</body>
</html>
"""


def convert_index() -> Path:
    dest = HTML_DIR / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render_site_index(discover_episode_files()), encoding="utf-8")
    return dest


def discover_character_files() -> list[Path]:
    if not CHARACTERS_DIR.exists():
        return []
    return sorted(
        path
        for path in CHARACTERS_DIR.glob("*.md")
        if path.stem not in CHARACTER_EXCLUDES
    )


def character_image_path(name: str) -> Path | None:
    references = CHARACTER_ASSETS_DIR / name / "references"
    for filename in ("main.png", "main.jpg", "main.jpeg", "main.webp"):
        candidate = references / filename
        if candidate.exists():
            return candidate
    return None


def render_character_card(source: Path) -> str:
    name = source.stem
    detail_href = f"characters/{name}.html"
    image = character_image_path(name)
    src = f"../{image.relative_to(ROOT)}"
    media = f'<img src="{html.escape(src, quote=True)}" alt="{html.escape(name, quote=True)}" loading="lazy">'
    return (
        f'<a class="card" href="{html.escape(detail_href, quote=True)}">'
        f"{media}"
        '<span class="card-text">'
        f"<strong>{html.escape(name)}</strong>"
        "</span>"
        "</a>"
    )


CHARACTER_INDEX_EXCLUDES = {"김용식"}


def characters_for_index(character_files: list[Path]) -> list[Path]:
    return [
        path
        for path in character_files
        if path.stem not in CHARACTER_INDEX_EXCLUDES and character_image_path(path.stem) is not None
    ]


def render_character_index(character_files: list[Path]) -> str:
    character_files = characters_for_index(character_files)
    cards = "\n      ".join(render_character_card(path) for path in character_files)
    if not cards:
        cards = '<p class="empty">등록된 인물 설정이 없습니다.</p>'
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>wish-real 인물</title>
  <style>{CHARACTER_INDEX_CSS}  </style>
</head>
<body>
  <main>
    <a class="top-link" href="index.html">목차</a>
    <div class="grid">
      {cards}
    </div>
  </main>
</body>
</html>
"""


def render_character_profile(source: Path) -> str:
    name = source.stem
    image = character_image_path(name)
    if image:
        src = f"../../{image.relative_to(ROOT)}"
        image_block = (
            f'<div class="portrait"><img src="{html.escape(src, quote=True)}" '
            f'alt="{html.escape(name, quote=True)}" onclick="openLightbox(this.src)"></div>'
        )
    else:
        image_block = f'<div class="portrait no-image"><span>{html.escape(name)}</span></div>'
    body = render_profile_markdown(source.read_text(encoding="utf-8"))
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(name)}</title>
  <style>{CHARACTER_PROFILE_CSS}  </style>
</head>
<body>
  <main>
    <a class="back" href="../characters.html">인물 목록</a>
    <section class="header">
      {image_block}
      <h1>{html.escape(name)}</h1>
    </section>
    <section class="profile-body">
{body}
    </section>
  </main>
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
    document.addEventListener('keydown', function(event) {{
      if (event.key === 'Escape') closeLightbox();
    }});
  </script>
</body>
</html>
"""


def convert_characters() -> list[Path]:
    character_files = discover_character_files()
    outputs: list[Path] = []
    index_path = HTML_DIR / "characters.html"
    detail_dir = HTML_DIR / "characters"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    detail_dir.mkdir(parents=True, exist_ok=True)

    index_path.write_text(render_character_index(character_files), encoding="utf-8")
    outputs.append(index_path)

    for source in character_files:
        dest = detail_dir / f"{source.stem}.html"
        dest.write_text(render_character_profile(source), encoding="utf-8")
        outputs.append(dest)

    return outputs


def convert_markdown_file(source: Path) -> Path:
    matched = EP_PATTERN.match(source.name)
    if not matched:
        raise ValueError(f"Episode filename must look like ep.001.md: {source}")

    ep_num = int(matched.group(1))
    dest = output_path_for_source(source)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render_episode(source.read_text(encoding="utf-8"), ep_num), encoding="utf-8")
    return dest


def convert_episode(ep_num: int) -> Path:
    src = episode_path(ep_num)
    if not src.exists():
        raise FileNotFoundError(f"Episode not found: {src}")
    return convert_markdown_file(src)


def discover_episode_files() -> list[Path]:
    return sorted(path for path in EPISODES_DIR.rglob("ep.*.md") if EP_PATTERN.match(path.name))


def parse_sources(args: list[str]) -> list[Path]:
    if not args:
        return discover_episode_files()

    sources: list[Path] = []
    for arg in args:
        candidate = Path(arg)
        if candidate.exists():
            sources.append(candidate)
            continue

        value = arg.removeprefix("ep.").removesuffix(".md")
        if value.isdigit():
            sources.append(episode_path(int(value)))
            continue

        raise ValueError(f"Cannot parse episode argument: {arg}")
    return sources


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="wish-real 에피소드 Markdown을 로컬 HTML로 변환합니다.")
    parser.add_argument("episodes", nargs="*", help="변환할 화수 또는 Markdown 경로. 예: 1, ep.001.md")
    parsed = parser.parse_args(argv)

    sources = parse_sources(parsed.episodes)
    if not sources:
        print("No episode markdown files found.", file=sys.stderr)
        return 1

    for source in sources:
        dest = convert_markdown_file(source)
        print(dest.relative_to(ROOT))
    index_dest = convert_index()
    print(index_dest.relative_to(ROOT))
    for dest in convert_characters():
        print(dest.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
