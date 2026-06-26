import subprocess
import unittest
from unittest.mock import patch

import convert_html


class PublishHtmlChangesTest(unittest.TestCase):
    def test_stages_html_commits_when_changed_and_pushes(self):
        calls = []

        def fake_run(cmd, cwd=None, check=False, capture_output=False, text=False):
            calls.append(cmd)
            if cmd == ["git", "diff", "--cached", "--quiet", "--", "html"]:
                return subprocess.CompletedProcess(cmd, 1, "", "")
            if cmd == ["git", "branch", "--show-current"]:
                return subprocess.CompletedProcess(cmd, 0, "main\n", "")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with patch.object(convert_html.subprocess, "run", fake_run):
            branch = convert_html.publish_html_changes()

        self.assertEqual(branch, "main")
        self.assertIn(["git", "add", "-A", "html"], calls)
        self.assertIn(["git", "commit", "-m", "chore: update generated html"], calls)
        self.assertIn(["git", "push", "origin", "main"], calls)

    def test_pushes_without_empty_commit_when_html_unchanged(self):
        calls = []

        def fake_run(cmd, cwd=None, check=False, capture_output=False, text=False):
            calls.append(cmd)
            if cmd == ["git", "diff", "--cached", "--quiet", "--", "html"]:
                return subprocess.CompletedProcess(cmd, 0, "", "")
            if cmd == ["git", "branch", "--show-current"]:
                return subprocess.CompletedProcess(cmd, 0, "main\n", "")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with patch.object(convert_html.subprocess, "run", fake_run):
            branch = convert_html.publish_html_changes()

        self.assertEqual(branch, "main")
        self.assertIn(["git", "add", "-A", "html"], calls)
        self.assertNotIn(["git", "commit", "-m", "chore: update generated html"], calls)
        self.assertIn(["git", "push", "origin", "main"], calls)


if __name__ == "__main__":
    unittest.main()
