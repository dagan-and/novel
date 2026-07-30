#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_MESSAGE = "Update wish-real"


def run_git(
    args: list[str],
    *,
    cwd: Path,
    check: bool = True,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=check,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def git_output(args: list[str], *, cwd: Path) -> str:
    return run_git(args, cwd=cwd, capture=True).stdout.strip()


def git_root(start: Path = PROJECT_DIR) -> Path:
    return Path(git_output(["rev-parse", "--show-toplevel"], cwd=start))


def current_branch(root: Path) -> str:
    branch = git_output(["branch", "--show-current"], cwd=root)
    if not branch:
        raise RuntimeError("Detached HEAD 상태라 푸시할 브랜치를 자동으로 정할 수 없습니다.")
    return branch


def project_pathspec(root: Path, project_dir: Path = PROJECT_DIR) -> str:
    return project_dir.relative_to(root).as_posix()


def changed_lines(root: Path, pathspec: str) -> list[str]:
    output = git_output(["status", "--short", "--", pathspec], cwd=root)
    return [line for line in output.splitlines() if line.strip()]


def has_staged_changes(root: Path, pathspec: str) -> bool:
    result = run_git(["diff", "--cached", "--quiet", "--", pathspec], cwd=root, check=False)
    return result.returncode == 1


def print_changes(lines: list[str]) -> None:
    print("wish-real 변경사항:")
    for line in lines:
        print(f"  {line}")


def push_wish_real(
    *,
    message: str,
    remote: str,
    branch: str | None,
    dry_run: bool,
    no_push: bool,
) -> int:
    root = git_root()
    pathspec = project_pathspec(root)
    target_branch = branch or current_branch(root)
    lines = changed_lines(root, pathspec)

    if not lines:
        print("wish-real 안에 커밋할 변경사항이 없습니다.")
        return 0

    print_changes(lines)

    if dry_run:
        print(f"\nDRY RUN: git add -A -- {pathspec}")
        print(f"DRY RUN: git commit -m {message!r}")
        if not no_push:
            print(f"DRY RUN: git push {remote} {target_branch}")
        return 0

    run_git(["add", "-A", "--", pathspec], cwd=root)

    if not has_staged_changes(root, pathspec):
        print("스테이징 후 커밋할 변경사항이 없습니다.")
        return 0

    run_git(["commit", "-m", message], cwd=root)

    if no_push:
        print("커밋까지 완료했습니다. --no-push 옵션 때문에 푸시는 건너뜁니다.")
        return 0

    run_git(["push", remote, target_branch], cwd=root)
    print(f"{remote}/{target_branch} 푸시 완료.")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="wish-real 폴더의 모든 변경사항만 스테이징, 커밋, 푸시합니다."
    )
    parser.add_argument(
        "-m",
        "--message",
        default=DEFAULT_MESSAGE,
        help=f"커밋 메시지. 기본값: {DEFAULT_MESSAGE!r}",
    )
    parser.add_argument("--remote", default="origin", help="푸시할 원격 이름. 기본값: origin")
    parser.add_argument(
        "--branch",
        help="푸시할 브랜치. 생략하면 현재 브랜치를 사용합니다.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 add/commit/push 없이 실행될 명령만 보여줍니다.",
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
        return push_wish_real(
            message=args.message,
            remote=args.remote,
            branch=args.branch,
            dry_run=args.dry_run,
            no_push=args.no_push,
        )
    except subprocess.CalledProcessError as exc:
        if exc.stdout:
            print(exc.stdout, file=sys.stderr)
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        return exc.returncode
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
