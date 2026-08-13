#!/usr/bin/env python3
"""Commit and push every change under outlines."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


DEFAULT_OUTLINE_DIR = "outlines"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MESSAGE = "Update outline files"
DEFAULT_REMOTE = "origin"


@dataclass(frozen=True)
class PushResult:
    committed: bool
    pushed: bool
    branch: str
    remote: str
    outline_dir: str


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
        raise RuntimeError("cannot push from detached HEAD")
    return branch


def has_outline_status(repo_root: Path, outline_dir: str, git: GitRunner = run_git) -> bool:
    result = git(["status", "--porcelain", "--", outline_dir], repo_root, True, True)
    return bool(result.stdout.strip())


def has_staged_outline_changes(
    repo_root: Path,
    outline_dir: str,
    git: GitRunner = run_git,
) -> bool:
    result = git(
        ["diff", "--cached", "--quiet", "--", outline_dir],
        repo_root,
        False,
        False,
    )
    return result.returncode != 0


def push_outlines(
    repo_root: Path,
    outline_dir: str = DEFAULT_OUTLINE_DIR,
    message: str = DEFAULT_MESSAGE,
    remote: str = DEFAULT_REMOTE,
    branch: str | None = None,
    force: bool = False,
    git: GitRunner = run_git,
) -> PushResult:
    repo_root = repo_root.resolve()
    target_branch = branch or current_branch(repo_root, git)

    if not has_outline_status(repo_root, outline_dir, git):
        return PushResult(
            committed=False,
            pushed=False,
            branch=target_branch,
            remote=remote,
            outline_dir=outline_dir,
        )

    git(["add", "-A", "--", outline_dir], repo_root, False, True)

    if not has_staged_outline_changes(repo_root, outline_dir, git):
        return PushResult(
            committed=False,
            pushed=False,
            branch=target_branch,
            remote=remote,
            outline_dir=outline_dir,
        )

    git(["commit", "-m", message, "--", outline_dir], repo_root, False, True)

    force_flag = "--force" if force else "--force-with-lease"
    git(["push", force_flag, remote, target_branch], repo_root, False, True)

    return PushResult(
        committed=True,
        pushed=True,
        branch=target_branch,
        remote=remote,
        outline_dir=outline_dir,
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Commit and push every git change under outlines only."
    )
    parser.add_argument("--repo-root", default=str(PROJECT_ROOT))
    parser.add_argument("--outline-dir", default=DEFAULT_OUTLINE_DIR)
    parser.add_argument("--message", default=DEFAULT_MESSAGE)
    parser.add_argument("--remote", default=DEFAULT_REMOTE)
    parser.add_argument("--branch", help="Defaults to the current branch.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Use git push --force instead of the default --force-with-lease.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = push_outlines(
        repo_root=Path(args.repo_root),
        outline_dir=args.outline_dir,
        message=args.message,
        remote=args.remote,
        branch=args.branch,
        force=args.force,
    )

    if result.pushed:
        print(f"Pushed {result.outline_dir} changes to {result.remote}/{result.branch}.")
    else:
        print(f"No {result.outline_dir} changes to push.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
