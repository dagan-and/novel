#!/usr/bin/env python3
"""Remove generated outline footer blocks from outline files."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path


TEXT_EXTENSIONS = {".txt"}
FOOTER_MARKER_PREFIX = "<!-- outline-footer:"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class FileResult:
    path: Path
    changed: bool


@dataclass(frozen=True)
class DirResult:
    scanned_count: int
    changed_count: int
    changed_paths: tuple[Path, ...]


def strip_footer(content: str) -> tuple[str, bool]:
    marker_index = content.find(FOOTER_MARKER_PREFIX)
    if marker_index == -1:
        return content, False

    remaining = content[:marker_index].rstrip()
    if remaining:
        remaining = f"{remaining}\n"
    return remaining, True


def remove_footer(path: Path) -> FileResult:
    content = path.read_text(encoding="utf-8")
    updated, changed = strip_footer(content)

    if changed:
        path.write_text(updated, encoding="utf-8")

    return FileResult(path=path, changed=changed)


def iter_outline_files(outline_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in outline_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS
    )


def remove_from_outline_dir(outline_dir: Path) -> DirResult:
    if not outline_dir.exists():
        raise FileNotFoundError(f"outline directory not found: {outline_dir}")

    changed_paths: list[Path] = []
    files = iter_outline_files(outline_dir)
    for path in files:
        result = remove_footer(path)
        if result.changed:
            changed_paths.append(path)

    return DirResult(
        scanned_count=len(files),
        changed_count=len(changed_paths),
        changed_paths=tuple(changed_paths),
    )


def display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove generated outline footer blocks from every .txt file in outlines."
    )
    parser.add_argument("--outline-dir", default="outlines")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = PROJECT_ROOT

    try:
        result = remove_from_outline_dir((repo_root / args.outline_dir).resolve())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Scanned: {result.scanned_count}")
    print(f"Changed: {result.changed_count}")
    for path in result.changed_paths:
        print(display_path(path, repo_root))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
