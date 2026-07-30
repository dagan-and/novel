#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_MESSAGE = "Update wish-real episodes"


def run_step(args: list[str]) -> None:
    subprocess.run(args, cwd=PROJECT_DIR, check=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="소설 작성 후 HTML 변환과 wish-real 푸시를 순서대로 실행합니다."
    )
    parser.add_argument(
        "episodes",
        nargs="*",
        help="HTML로 변환할 화수 또는 Markdown 경로. 생략하면 전체 에피소드를 변환합니다.",
    )
    parser.add_argument(
        "-m",
        "--message",
        default=DEFAULT_MESSAGE,
        help=f"커밋 메시지. 기본값: {DEFAULT_MESSAGE!r}",
    )
    parser.add_argument("--remote", default="origin", help="푸시할 원격 이름. 기본값: origin")
    parser.add_argument("--branch", help="푸시할 브랜치. 생략하면 현재 브랜치를 사용합니다.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="push_wish_real.py에 dry-run을 전달합니다. HTML 변환은 실제 실행합니다.",
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="스테이징과 커밋만 하고 푸시는 건너뜁니다.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        run_step([sys.executable, "convert_html.py", *args.episodes])

        push_args = [
            sys.executable,
            "push_wish_real.py",
            "-m",
            args.message,
            "--remote",
            args.remote,
        ]
        if args.branch:
            push_args.extend(["--branch", args.branch])
        if args.dry_run:
            push_args.append("--dry-run")
        if args.no_push:
            push_args.append("--no-push")

        run_step(push_args)
    except subprocess.CalledProcessError as exc:
        return exc.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
