"""
ep.NNN_a.md → ep.NNN.md 일괄 변환
"""

import os
import re
from pathlib import Path

EPISODES_DIR = Path(__file__).parent / "episodes"


def main(dry_run: bool = False):
    targets = sorted(EPISODES_DIR.rglob("ep.*_a.md"))

    if not targets:
        print("변환 대상 파일 없음.")
        return

    for src in targets:
        dst = src.with_name(re.sub(r"_a\.md$", ".md", src.name))

        if dst.exists():
            print(f"SKIP (충돌): {src.relative_to(EPISODES_DIR)}")
            continue

        if dry_run:
            print(f"DRY  {src.relative_to(EPISODES_DIR)}  →  {dst.name}")
        else:
            src.rename(dst)
            print(f"OK   {src.relative_to(EPISODES_DIR)}  →  {dst.name}")


if __name__ == "__main__":
    import sys

    dry = "--dry" in sys.argv
    if dry:
        print("=== DRY RUN (실제 변경 없음) ===")
    main(dry_run=dry)
