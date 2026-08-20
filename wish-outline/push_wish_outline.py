#!/usr/bin/env python3
"""Commit and push every Git change under the wish-outline folder only."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_REPO_ROOT = PROJECT_ROOT.parent
DEFAULT_PROJECT_DIR = PROJECT_ROOT.name
DEFAULT_MESSAGE = "Update wish-outline"
DEFAULT_REMOTE = "origin"


@dataclass(frozen=True)
class PushResult:
    committed: bool
    pushed: bool
    branch: str
    remote: str
    project_dir: str


GitRunner = Callable[[list[str], Path, bool, bool], subprocess.CompletedProcess[str]]


def run_git(
    args: list[str],
    cwd: Path,
    capture: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=capture,
        check=check,
    )


def current_branch(repo_root: Path, git: GitRunner = run_git) -> str:
    result = git(["branch", "--show-current"], repo_root, True, True)
    branch = result.stdout.strip()
    if not branch:
        raise RuntimeError("detached HEAD 상태라서 푸시할 브랜치를 알 수 없습니다.")
    return branch


def has_project_status(
    repo_root: Path,
    project_dir: str,
    git: GitRunner = run_git,
) -> bool:
    result = git(["status", "--porcelain", "--", project_dir], repo_root, True, True)
    return bool(result.stdout.strip())


def has_staged_project_changes(
    repo_root: Path,
    project_dir: str,
    git: GitRunner = run_git,
) -> bool:
    result = git(
        ["diff", "--cached", "--quiet", "--", project_dir],
        repo_root,
        False,
        False,
    )
    return result.returncode != 0


def push_wish_outline(
    repo_root: Path = DEFAULT_REPO_ROOT,
    project_dir: str = DEFAULT_PROJECT_DIR,
    message: str = DEFAULT_MESSAGE,
    remote: str = DEFAULT_REMOTE,
    branch: str | None = None,
    git: GitRunner = run_git,
) -> PushResult:
    repo_root = repo_root.resolve()
    target_branch = branch or current_branch(repo_root, git)

    if not has_project_status(repo_root, project_dir, git):
        return PushResult(
            committed=False,
            pushed=False,
            branch=target_branch,
            remote=remote,
            project_dir=project_dir,
        )

    git(["add", "-A", "--", project_dir], repo_root, False, True)

    if not has_staged_project_changes(repo_root, project_dir, git):
        return PushResult(
            committed=False,
            pushed=False,
            branch=target_branch,
            remote=remote,
            project_dir=project_dir,
        )

    git(["commit", "-m", message, "--", project_dir], repo_root, False, True)
    git(["push", remote, target_branch], repo_root, False, True)

    return PushResult(
        committed=True,
        pushed=True,
        branch=target_branch,
        remote=remote,
        project_dir=project_dir,
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Commit and push every change under wish-outline only."
    )
    parser.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    parser.add_argument("--project-dir", default=DEFAULT_PROJECT_DIR)
    parser.add_argument("--message", default=DEFAULT_MESSAGE)
    parser.add_argument("--remote", default=DEFAULT_REMOTE)
    parser.add_argument("--branch", help="기본값은 현재 브랜치입니다.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = push_wish_outline(
        repo_root=Path(args.repo_root),
        project_dir=args.project_dir,
        message=args.message,
        remote=args.remote,
        branch=args.branch,
    )

    if result.pushed:
        print(f"{result.project_dir} 변경사항을 {result.remote}/{result.branch}에 푸시했습니다.")
    else:
        print(f"{result.project_dir} 안에 푸시할 변경사항이 없습니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
