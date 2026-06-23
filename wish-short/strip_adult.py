#!/usr/bin/env python3
"""
strip_adult.py — 성인씬 블록 이후 본문 텍스트 제거

[sex] 마커 이후에 추가된 노골적 본문을 삭제하고,
성인씬 컨텍스트 블록까지는 원본 그대로 유지합니다.

사용법:
  python3 strip_adult.py 96               단일 화수
  python3 strip_adult.py 96-110           범위
  python3 strip_adult.py 96,97,98         목록 (쉼표 구분)
  python3 strip_adult.py 96-110 --out ./clean   출력 디렉토리 지정

기본 출력: 원본 파일 덮어쓰기 (변경 없으면 건너뜀)
          --out 지정 시 해당 디렉토리에 같은 파일명으로 저장
"""

import sys
import os
from pathlib import Path

EPISODES_DIR = Path(__file__).parent / "episodes" / "001-100"
PROGRESS_MARKER = "<progress>[sex]</progress>"


def parse_episodes(arg: str):
    """106, 106-110, 106,107,108 형식 파싱."""
    episodes = set()
    for token in arg.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            parts = token.split("-", 1)
            try:
                start, end = int(parts[0]), int(parts[1])
            except ValueError:
                print(f"오류: 범위 형식이 잘못됐습니다 — '{token}'", file=sys.stderr)
                sys.exit(1)
            if start > end:
                print(f"오류: 범위 시작({start})이 끝({end})보다 큽니다.", file=sys.stderr)
                sys.exit(1)
            episodes.update(range(start, end + 1))
        else:
            try:
                episodes.add(int(token))
            except ValueError:
                print(f"오류: 숫자가 아닙니다 — '{token}'", file=sys.stderr)
                sys.exit(1)
    return sorted(episodes)


def find_episode_file(ep_num: int):
    """에피소드 번호로 파일 탐색. _a 버전 우선."""
    for suffix in ["_a", ""]:
        path = EPISODES_DIR / f"ep.{ep_num:03d}{suffix}.md"
        if path.exists():
            return path
    return None


def strip_after_progress(content: str):
    """
    <progress>[sex]</progress> 마커가 있는 줄까지 유지하고 이후를 제거.
    마커 뒤에 아무것도 없으면 (이미 clean) 변경 없음으로 반환.
    반환: (처리된_내용, 변경_여부)
    """
    idx = content.find(PROGRESS_MARKER)
    if idx == -1:
        return content, False

    # 마커가 끝나는 위치
    end_of_marker = idx + len(PROGRESS_MARKER)

    # 마커 이후가 공백·줄바꿈·--- 만 이면 이미 clean
    remainder = content[end_of_marker:]
    remainder_stripped = remainder.strip().strip("-").strip()
    if not remainder_stripped:
        return content, False

    # 마커 줄까지만 유지, 이후 전부 제거
    kept = content[:end_of_marker].rstrip()
    return kept + "\n\n---\n", True


def resolve_output_path(src: Path, out_dir):
    if out_dir:
        return out_dir / src.name
    # 기본: 원본 덮어쓰기
    return src


def usage():
    print(__doc__.strip())


def main():
    args = sys.argv[1:]

    if not args:
        print("오류: 화수 또는 범위를 입력해야 합니다.", file=sys.stderr)
        print("", file=sys.stderr)
        usage()
        sys.exit(1)

    ep_arg = args[0]
    out_dir = None

    # --out 옵션 파싱
    i = 1
    while i < len(args):
        if args[i] == "--out" and i + 1 < len(args):
            out_dir = Path(args[i + 1])
            out_dir.mkdir(parents=True, exist_ok=True)
            i += 2
        else:
            print(f"오류: 알 수 없는 옵션 — '{args[i]}'", file=sys.stderr)
            usage()
            sys.exit(1)

    episodes = parse_episodes(ep_arg)
    if not episodes:
        print("오류: 유효한 화수가 없습니다.", file=sys.stderr)
        sys.exit(1)

    print(f"처리 대상: {len(episodes)}편 ({episodes[0]}~{episodes[-1]})")
    print()

    found = stripped = skipped = 0

    for ep_num in episodes:
        src = find_episode_file(ep_num)
        if not src:
            print(f"  건너뜀 ep.{ep_num:03d} — 파일 없음")
            skipped += 1
            continue

        found += 1
        content = src.read_text(encoding="utf-8")
        new_content, changed = strip_after_progress(content)

        if not changed:
            print(f"  건너뜀 {src.name} — 추가 본문 없음 (이미 clean)")
            skipped += 1
            continue

        out_path = resolve_output_path(src, out_dir)
        out_path.write_text(new_content, encoding="utf-8")
        stripped += 1
        label = "덮어씀" if out_path == src else f"→  {out_path.name}"
        print(f"  ✓  {src.name}  {label}")

    print()
    print(f"완료: {found}개 파일 발견 / {stripped}개 처리 / {skipped}개 건너뜀")


if __name__ == "__main__":
    main()
