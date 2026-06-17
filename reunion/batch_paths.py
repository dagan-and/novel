#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path


BATCH_SIZE = 100
EPISODE_PATTERN = re.compile(r"^ep\.(\d+)(?:_a)?$")
EPISODE_FILE_PATTERN = re.compile(r"^ep\.(\d+)(?:_a)?\.(?:md|html)$")


def episode_number(value: str | Path) -> int:
    if isinstance(value, Path):
        name = value.stem
    else:
        name = str(value).replace(".md", "").replace(".html", "").replace(".txt", "")
    match = EPISODE_PATTERN.match(name)
    if not match:
        raise ValueError(f"에피소드 번호를 해석할 수 없습니다: {value}")
    return int(match.group(1))


def batch_bounds(ep_num: int) -> tuple[int, int]:
    start = ((ep_num - 1) // BATCH_SIZE) * BATCH_SIZE + 1
    end = start + BATCH_SIZE - 1
    return start, end


def batch_label(ep_num: int) -> str:
    start, end = batch_bounds(ep_num)
    return f"{start:03d}-{end:03d}"


def batched_relative_path(filename: str, extension: str) -> Path:
    ep_num = episode_number(filename)
    stem = str(filename).replace(".md", "").replace(".html", "").replace(".txt", "")
    return Path(batch_label(ep_num)) / f"{stem}.{extension}"


def source_episode_path(base_dir: Path, episode_name: str) -> Path:
    preferred = base_dir / "episodes" / batched_relative_path(episode_name, "md")
    if preferred.exists():
        return preferred

    legacy = base_dir / "episodes" / f"{Path(episode_name).stem}.md"
    if legacy.exists():
        return legacy

    for path in sorted((base_dir / "episodes").rglob(f"{Path(episode_name).stem}.md")):
        return path
    raise FileNotFoundError(f"에피소드 파일이 없습니다: {episode_name}")


def html_episode_path(base_dir: Path, episode_name: str) -> Path:
    return base_dir / "html" / batched_relative_path(episode_name, "html")


def prompt_output_path(base_dir: Path, episode_name: str) -> Path:
    stem = str(episode_name).replace(".md", "").replace(".html", "")
    return base_dir / "images" / "prompt" / batched_relative_path(f"{stem}.prompt", "txt")


def prelude_output_path(base_dir: Path, episode_name: str, suffix: str) -> Path:
    stem = str(episode_name).replace(".md", "").replace(".html", "")
    return base_dir / "images" / "preludes" / batch_label(episode_number(episode_name)) / f"{stem}.{suffix}"


def iter_episode_files(root: Path, suffix: str) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        (
            path
            for path in root.rglob(f"*.{suffix}")
            if EPISODE_FILE_PATTERN.match(path.name)
        ),
        key=lambda path: (episode_number(path), "_a" in path.stem, path.as_posix()),
    )
