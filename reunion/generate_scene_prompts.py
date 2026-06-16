#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EPISODES_DIR = ROOT / "episodes"
CHARACTER_IMAGES_DIR = ROOT / "images" / "characters"
PROMPT_DIR = ROOT / "images" / "prompt"
COMMON_PROMPT_PATH = PROMPT_DIR / "common_scene_prompt.txt"

SAFE_SECTION_ORDER = [
    "장소",
    "등장인물",
    "의상",
    "이미지 포인트",
    "표정 포인트",
    "손 / 시선 포인트",
    "복장 상태",
    "배경 소품 강조",
    "소품 / 환경",
    "분위기 키워드",
]

SKIP_PREFIXES = {
    "호칭",
    "직전 맥락",
    "관계 단계",
    "현재 구도",
    "합의 상태",
    "씬 이후 감정 방향",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build safe image prompt files from episode adult-scene metadata."
    )
    parser.add_argument(
        "episodes",
        nargs="*",
        help="Episode numbers or files. Example: 092 ep.137 episodes/ep.092.md",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate prompts for every episode that contains an adult-scene block.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(PROMPT_DIR),
        help="Directory to write prompt files.",
    )
    parser.add_argument(
        "--template",
        default=str(COMMON_PROMPT_PATH),
        help="Common prompt text file.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing prompt files.",
    )
    return parser.parse_args()


def resolve_episode_path(raw: str) -> Path:
    path = Path(raw)
    if path.exists():
        return path.resolve()

    digits = re.search(r"(\d{1,3})", raw)
    if not digits:
        raise SystemExit(f"화수를 해석할 수 없습니다: {raw}")
    ep_no = int(digits.group(1))
    candidate = EPISODES_DIR / f"ep.{ep_no:03d}.md"
    if not candidate.exists():
        raise SystemExit(f"에피소드 파일이 없습니다: {candidate}")
    return candidate


def adult_episode_paths() -> list[Path]:
    paths: list[Path] = []
    for path in sorted(EPISODES_DIR.glob("ep.*.md")):
        if "성인씬 #" in path.read_text(encoding="utf-8"):
            paths.append(path)
    return paths


def extract_scene_block(text: str) -> tuple[str, list[str]]:
    lines = text.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if line.startswith("##") and "성인씬 #" in line:
            start = idx
            break
    if start is None:
        raise ValueError("성인씬 블록을 찾지 못했습니다.")

    block_lines = [lines[start].rstrip()]
    for line in lines[start + 1 :]:
        block_lines.append(line.rstrip())
        if "<progress>" in line:
            break
    return block_lines[0], block_lines[1:]


def parse_safe_sections(block_lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {key: [] for key in SAFE_SECTION_ORDER}
    current: str | None = None

    for raw_line in block_lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if "<progress>" in stripped:
            break

        top_match = re.match(r"^- ([^:]+):\s*(.*)$", line)
        if top_match:
            label = top_match.group(1).strip()
            value = top_match.group(2).strip()

            if label in SKIP_PREFIXES:
                current = None
                continue

            if label in SAFE_SECTION_ORDER:
                current = label
                if value:
                    sections[label].append(f"- {value}")
                continue

            current = None
            continue

        if current is None:
            continue
        if "누적 성인씬 횟수" in stripped:
            continue
        sections[current].append(line)

    return {key: value for key, value in sections.items() if value}


def extract_episode_label(heading: str, episode_path: Path) -> str:
    match = re.search(r"ep\.(\d{3})", heading)
    if match:
        return f"ep.{match.group(1)}"
    match = re.search(r"ep\.(\d{3})", episode_path.name)
    if match:
        return f"ep.{match.group(1)}"
    return episode_path.stem


def collect_character_names(sections: dict[str, list[str]]) -> list[str]:
    names: list[str] = []
    for line in sections.get("등장인물", []):
        match = re.match(r"\s*-\s*([가-힣]+):", line)
        if match:
            names.append(match.group(1))
    return names


def find_character_image(name: str) -> Path | None:
    for ext in ("png", "jpg", "jpeg", "webp"):
        candidate = CHARACTER_IMAGES_DIR / f"{name}.{ext}"
        if candidate.exists():
            return candidate
    return None


def build_prompt(template_text: str, episode_label: str, sections: dict[str, list[str]]) -> str:
    parts = [template_text.strip(), "", episode_label, ""]

    for section_name in SAFE_SECTION_ORDER:
        values = sections.get(section_name)
        if not values:
            continue
        parts.append(f"- {section_name}:")
        parts.extend(values)
        parts.append("")

    return "\n".join(parts).strip() + "\n"


def write_text(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"이미 존재합니다: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    template_text = Path(args.template).read_text(encoding="utf-8")
    output_dir = Path(args.output_dir)

    if args.all:
        episode_paths = adult_episode_paths()
    else:
        if not args.episodes:
            raise SystemExit("화수를 지정하거나 --all 옵션을 사용해주세요.")
        episode_paths = [resolve_episode_path(raw) for raw in args.episodes]

    for episode_path in episode_paths:
        raw = episode_path.read_text(encoding="utf-8")
        heading, block_lines = extract_scene_block(raw)
        sections = parse_safe_sections(block_lines)
        episode_label = extract_episode_label(heading, episode_path)
        prompt = build_prompt(template_text, episode_label, sections)
        output_path = output_dir / f"{episode_label}.prompt.txt"
        write_text(output_path, prompt, force=args.force)
        print(f"[prompt] {episode_label} -> {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
