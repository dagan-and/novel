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


class HtmlMapTests(unittest.TestCase):
    def test_generate_includes_current_territory_map_section(self):
        state = {
            "year": 25,
            "long_term_goal": "마한 통일",
            "turn": 25,
            "identity": {
                "name": "금휘 (金煇)",
                "role": "영산 군정국 수장",
                "location": "영산강·목포 해안권",
                "apparent_age": 40,
            },
            "stats": {
                "tribal_influence": 15,
                "population_under_influence": 2190,
            },
        }

        html = generate.generate(state, [], [])

        self.assertIn("현재 판도", html)
        self.assertIn("영산 본진", html)
        self.assertIn("목포 해안", html)
        self.assertIn("을지 영향권", html)


if __name__ == "__main__":
    unittest.main()
