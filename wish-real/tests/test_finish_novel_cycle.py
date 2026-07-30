import unittest

import finish_novel_cycle


class FinishNovelCycleTests(unittest.TestCase):
    def test_parse_args_accepts_episodes_and_message(self):
        args = finish_novel_cycle.parse_args(["11", "12", "-m", "Add episodes 11-12"])

        self.assertEqual(["11", "12"], args.episodes)
        self.assertEqual("Add episodes 11-12", args.message)
        self.assertEqual("origin", args.remote)
        self.assertIsNone(args.branch)
        self.assertFalse(args.dry_run)
        self.assertFalse(args.no_push)

    def test_parse_args_accepts_push_options(self):
        args = finish_novel_cycle.parse_args(
            ["--remote", "upstream", "--branch", "main", "--dry-run", "--no-push"]
        )

        self.assertEqual([], args.episodes)
        self.assertEqual("upstream", args.remote)
        self.assertEqual("main", args.branch)
        self.assertTrue(args.dry_run)
        self.assertTrue(args.no_push)


if __name__ == "__main__":
    unittest.main()
