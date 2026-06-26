#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EPISODES_DIR = ROOT / "episodes"
HTML_DIR = ROOT / "html"

EP_PATTERN = re.compile(r"ep\.(\d+)(?:_a)?\.md$")
DIALOGUE_PATTERN = re.compile(r"^\[(.+?)\]\s+\"(.*)\"$")
YONGSIK_SPEAKERS = {"김용식", "용식"}
FEMALE_SPEAKERS = {
    "소영",
    "아내",
    "손한나",
    "한나",
    "이은주",
    "은주",
    "박다정",
    "다정",
    "어머니",
}


def batch_label(ep_num: int) -> str:
    start = ((ep_num - 1) // 100) * 100 + 1
    end = start + 99
    return f"{start:03d}-{end:03d}"


def episode_path(ep_num: int) -> Path:
    return EPISODES_DIR / batch_label(ep_num) / f"ep.{ep_num:03d}.md"


def output_path(ep_num: int) -> Path:
    return HTML_DIR / batch_label(ep_num) / f"ep.{ep_num:03d}.html"


def html_link_path(ep_num: int) -> str:
    return f"/novel/dual_life/html/{batch_label(ep_num)}/ep.{ep_num:03d}.html"


def nav_item(label: str, ep_num: int | None) -> str:
    if ep_num is None:
        return f'<span class="nav-link disabled">{html.escape(label)}</span>'
    return f'<a class="nav-link" href="{html_link_path(ep_num)}">{html.escape(label)}</a>'


def render_navigation(ep_num: int) -> str:
    prev_ep = ep_num - 1 if episode_path(ep_num - 1).exists() else None
    next_ep = ep_num + 1 if episode_path(ep_num + 1).exists() else None
    index_href = "/novel/"
    return (
        '<nav class="episode-nav" aria-label="Episode navigation">'
        f"{nav_item('이전화', prev_ep)}"
        f'<a class="nav-link index-link" href="{index_href}">목록</a>'
        f"{nav_item('다음화', next_ep)}"
        "</nav>"
    )


def dialogue_class(speaker: str) -> str:
    if speaker in YONGSIK_SPEAKERS:
        return "dialogue speaker-yongsik"
    if speaker in FEMALE_SPEAKERS:
        return "dialogue speaker-female"
    return "dialogue"


def render_block(block: list[str]) -> str:
    if not block:
        return ""

    if len(block) == 1 and block[0].startswith("# "):
        title = html.escape(block[0][2:])
        return f"<h1>{title}</h1>"

    if len(block) == 1 and block[0].startswith("> "):
        quote = html.escape(block[0][2:])
        return f"<blockquote>{quote}</blockquote>"

    if len(block) == 1 and block[0] == "---":
        return '<div class="divider">* * *</div>'

    if len(block) == 1:
        matched = DIALOGUE_PATTERN.match(block[0])
        if matched:
            speaker_name = matched.group(1)
            speaker = html.escape(speaker_name)
            line = html.escape(matched.group(2))
            return (
                f'<p class="{dialogue_class(speaker_name)}">'
                f'<span class="speaker">[{speaker}]</span> '
                f'<span class="line">"{line}"</span>'
                "</p>"
            )

    escaped = "<br>\n".join(html.escape(line) for line in block)
    return f"<p>{escaped}</p>"


def render_episode(text: str, ep_num: int) -> str:
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        lines = lines[1:]

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

    rendered = "\n".join(render_block(block) for block in blocks if block)
    nav = render_navigation(ep_num)
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dual Life Episode</title>
  <style>
    :root {{
      color-scheme: dark light;
      --bg: #1d1b1a;
      --panel: #262321;
      --text: #ded6cd;
      --muted: #aba095;
      --accent: #d0a07f;
      --quote: #c9beb3;
      --quote-border: #6f6257;
      --divider: #7f7267;
      --yongsik-blue: #7db8ff;
      --female-pink: #ff9fca;
    }}
    @media (prefers-color-scheme: light) {{
      :root {{
        --bg: #ece5db;
        --panel: #f5efe7;
        --text: #312b27;
        --muted: #74695f;
        --accent: #8b5d44;
        --quote: #5d5046;
        --quote-border: #cab4a1;
        --divider: #9e8f80;
        --yongsik-blue: #1f66c2;
        --female-pink: #c23f78;
      }}
    }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: "Iowan Old Style", "Apple SD Gothic Neo", "Noto Serif KR", serif;
      line-height: 1.9;
    }}
    main {{
      max-width: 760px;
      margin: 0 auto;
      padding: 48px 20px 80px;
      background: var(--panel);
    }}
    h1 {{
      font-size: 2rem;
      margin: 0 0 2rem;
      line-height: 1.3;
    }}
    p, blockquote {{
      font-size: 1.06rem;
      margin: 0 0 1rem;
      white-space: normal;
    }}
    .dialogue .speaker {{
      font-weight: 700;
      color: var(--accent);
    }}
    .dialogue.speaker-yongsik .speaker,
    .dialogue.speaker-yongsik .line {{
      color: var(--yongsik-blue);
    }}
    .dialogue.speaker-female .speaker,
    .dialogue.speaker-female .line {{
      color: var(--female-pink);
    }}
    blockquote {{
      margin-left: 0;
      padding-left: 1rem;
      border-left: 3px solid var(--quote-border);
      color: var(--quote);
    }}
    .divider {{
      text-align: center;
      color: var(--divider);
      margin: 2rem 0;
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
      min-width: 112px;
      padding: 12px 16px;
      border: 1px solid var(--quote-border);
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.04);
      color: var(--text);
      text-align: center;
      text-decoration: none;
      font-size: 0.98rem;
    }}
    .nav-link:hover {{
      background: rgba(255, 255, 255, 0.08);
    }}
    .nav-link.disabled {{
      color: var(--muted);
      opacity: 0.5;
      pointer-events: none;
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


def convert_episode(ep_num: int) -> Path:
    src = episode_path(ep_num)
    if not src.exists():
        raise FileNotFoundError(f"Episode not found: {src}")

    dest = output_path(ep_num)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        render_episode(src.read_text(encoding="utf-8"), ep_num),
        encoding="utf-8",
    )
    return dest


def parse_args(args: list[str]) -> list[int]:
    if not args:
        episodes: list[int] = []
        for path in sorted(EPISODES_DIR.rglob("ep.*.md")):
            matched = EP_PATTERN.match(path.name)
            if matched:
                episodes.append(int(matched.group(1)))
        return episodes

    parsed: list[int] = []
    for arg in args:
        matched = EP_PATTERN.match(arg if arg.endswith(".md") else f"{arg}.md")
        if matched:
            parsed.append(int(matched.group(1)))
        else:
            parsed.append(int(arg))
    return parsed


def current_branch() -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    branch = result.stdout.strip()
    if not branch:
        raise RuntimeError("현재 브랜치를 확인할 수 없습니다.")
    return branch


def push_current_branch() -> str:
    branch = current_branch()
    subprocess.run(["git", "push", "origin", branch], cwd=ROOT, check=True)
    return branch


def stage_html_dir() -> None:
    subprocess.run(["git", "add", "-A", "html"], cwd=ROOT, check=True)


def has_staged_html_changes() -> bool:
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", "html"],
        cwd=ROOT,
        check=False,
    )
    if result.returncode == 0:
        return False
    if result.returncode == 1:
        return True
    raise RuntimeError("HTML 변경 사항 확인에 실패했습니다.")


def commit_staged_html_changes() -> bool:
    if not has_staged_html_changes():
        return False
    subprocess.run(
        ["git", "commit", "-m", "chore: update generated html"],
        cwd=ROOT,
        check=True,
    )
    return True


def publish_html_changes() -> str:
    stage_html_dir()
    commit_staged_html_changes()
    return push_current_branch()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="에피소드 Markdown을 HTML로 변환하고 html 폴더 전체를 원격에 푸시합니다."
    )
    parser.add_argument("episodes", nargs="*", help="변환할 에피소드 번호")
    parsed_args = parser.parse_args(sys.argv[1:])

    episode_numbers = parse_args(parsed_args.episodes)
    for ep_num in episode_numbers:
        dest = convert_episode(ep_num)
        print(dest.relative_to(ROOT))

    branch = publish_html_changes()
    print(f"pushed origin/{branch}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
