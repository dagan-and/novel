from pathlib import Path
import tempfile
import unittest

import push_wish_real


class PushWishRealTests(unittest.TestCase):
    def test_project_pathspec_uses_repo_relative_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "wish-real"
            project.mkdir()

            self.assertEqual("wish-real", push_wish_real.project_pathspec(root, project))

    def test_parse_args_defaults_to_origin_and_current_branch(self):
        args = push_wish_real.parse_args([])

        self.assertEqual("origin", args.remote)
        self.assertIsNone(args.branch)
        self.assertEqual("Update wish-real", args.message)
        self.assertFalse(args.dry_run)
        self.assertFalse(args.no_push)

    def test_parse_args_accepts_safety_options(self):
        args = push_wish_real.parse_args(
            ["--dry-run", "--no-push", "--branch", "main", "-m", "Add episode"]
        )

        self.assertTrue(args.dry_run)
        self.assertTrue(args.no_push)
        self.assertEqual("main", args.branch)
        self.assertEqual("Add episode", args.message)


if __name__ == "__main__":
    unittest.main()
