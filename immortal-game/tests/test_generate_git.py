import subprocess
import unittest

import generate


class GitPublishTests(unittest.TestCase):
    def test_publish_changes_stages_known_files_commits_and_pushes(self):
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            if cmd[:2] == ["diff", "--cached"] and "--name-only" in cmd:
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
            if cmd[:2] == ["diff", "--cached"] and "--quiet" in cmd:
                return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="")
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        result = generate.publish_to_git(
            files=["game-state.json", "events.json"],
            message="test commit",
            runner=fake_run,
        )

        self.assertEqual(result, "pushed")
        self.assertIn(["add", "--", "game-state.json", "events.json"], calls)
        self.assertIn(["commit", "-m", "test commit"], calls)
        self.assertIn(["push"], calls)


if __name__ == "__main__":
    unittest.main()
