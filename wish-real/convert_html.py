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

EP_PATTERN = re.compile(r"^ep\.(\d+)(?P<suffix>_a|\.sample)?\.md$")
DIALOGUE_PATTERN = re.compile(r'^\[(?P<speaker>.+?)\]\s+"(?P<line>.*)"$')
MESSAGE_PATTERN = re.compile(r"^\[(?P<sender>.+?)\]\s+(?P<body>.+)$")
IMAGE_PATTERN = re.compile(r"^!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]+)\)$")


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
      font-size: 1.9rem;
    }}
    h2 {{
      margin: 2rem 0 1rem;
      font-size: 1.35rem;
    }}
    p, blockquote {{
      margin: 0 0 1rem;
      font-size: 1.06rem;
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
