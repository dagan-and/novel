import subprocess
import unittest
from pathlib import Path

import push_wish_outline


class GitRecorder:
    def __init__(self, branch="main", status=" M wish-outline/generate_outlines.py\n M wish-short/notes.txt\n"):
        self.branch = branch
        self.status = status
        self.calls = []

    def __call__(self, args, cwd, capture=False, check=True):
        self.calls.append((args, cwd, capture, check))
        if args == ["branch", "--show-current"]:
            return subprocess.CompletedProcess(args, 0, stdout=self.branch, stderr="")
        if args == ["status", "--porcelain", "--", "wish-outline"]:
            return subprocess.CompletedProcess(args, 0, stdout=self.status, stderr="")
        if args == ["diff", "--cached", "--quiet", "--", "wish-outline"]:
            return subprocess.CompletedProcess(args, 1, stdout="", stderr="")
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")


class PushWishOutlineTests(unittest.TestCase):
    def test_pushes_only_wish_outline_changes_from_parent_repo(self):
        git = GitRecorder()
        repo_root = Path("/repo")

        result = push_wish_outline.push_wish_outline(
            repo_root=repo_root,
            project_dir="wish-outline",
            message="Update wish-outline",
            git=git,
        )

        self.assertTrue(result.pushed)
        self.assertEqual(
            [call[0] for call in git.calls],
            [
                ["branch", "--show-current"],
                ["status", "--porcelain", "--", "wish-outline"],
                ["add", "-A", "--", "wish-outline"],
                ["diff", "--cached", "--quiet", "--", "wish-outline"],
                ["commit", "-m", "Update wish-outline", "--", "wish-outline"],
                ["push", "origin", "main"],
            ],
        )

    def test_skips_commit_when_wish_outline_has_no_changes(self):
        git = GitRecorder(status="")

        result = push_wish_outline.push_wish_outline(
            repo_root=Path("/repo"),
            project_dir="wish-outline",
            git=git,
        )

        self.assertFalse(result.committed)
        self.assertFalse(result.pushed)
        self.assertNotIn(["add", "-A", "--", "wish-outline"], [call[0] for call in git.calls])


if __name__ == "__main__":
    unittest.main()
