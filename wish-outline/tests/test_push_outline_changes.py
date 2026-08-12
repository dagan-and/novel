import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "push_outline_changes.py"


def load_module():
    spec = importlib.util.spec_from_file_location("push_outline_changes", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeGit:
    def __init__(self, status=" M 05_outline/1화.txt\n", staged_has_changes=True):
        self.commands = []
        self.status = status
        self.staged_has_changes = staged_has_changes

    def __call__(self, args, cwd, capture=False, check=True):
        self.commands.append((tuple(args), Path(cwd), capture, check))
        if args[:2] == ["branch", "--show-current"]:
            return self.result(stdout="main\n")
        if args[:3] == ["status", "--porcelain", "--"]:
            return self.result(stdout=self.status)
        if args[:4] == ["diff", "--cached", "--quiet", "--"]:
            return self.result(returncode=1 if self.staged_has_changes else 0)
        return self.result()

    @staticmethod
    def result(stdout="", returncode=0):
        class Result:
            pass

        result = Result()
        result.stdout = stdout
        result.returncode = returncode
        return result


class PushOutlineChangesTests(unittest.TestCase):
    def test_pushes_only_outline_changes_with_force_with_lease_by_default(self):
        module = load_module()
        fake_git = FakeGit()
        repo = Path("/repo")

        result = module.push_outline_changes(repo, git=fake_git)

        command_args = [entry[0] for entry in fake_git.commands]
        self.assertEqual(
            command_args,
            [
                ("branch", "--show-current"),
                ("status", "--porcelain", "--", "05_outline"),
                ("add", "-A", "--", "05_outline"),
                ("diff", "--cached", "--quiet", "--", "05_outline"),
                ("commit", "-m", "Update outline files", "--", "05_outline"),
                ("push", "--force-with-lease", "origin", "main"),
            ],
        )
        self.assertTrue(result.committed)
        self.assertTrue(result.pushed)

    def test_allows_explicit_force_push(self):
        module = load_module()
        fake_git = FakeGit()

        module.push_outline_changes(Path("/repo"), force=True, git=fake_git)

        self.assertIn(
            (("push", "--force", "origin", "main"), Path("/repo"), False, True),
            fake_git.commands,
        )

    def test_skips_commit_and_push_when_outline_has_no_changes(self):
        module = load_module()
        fake_git = FakeGit(status="")

        result = module.push_outline_changes(Path("/repo"), git=fake_git)

        command_args = [entry[0] for entry in fake_git.commands]
        self.assertEqual(
            command_args,
            [
                ("branch", "--show-current"),
                ("status", "--porcelain", "--", "05_outline"),
            ],
        )
        self.assertFalse(result.committed)
        self.assertFalse(result.pushed)


if __name__ == "__main__":
    unittest.main()
