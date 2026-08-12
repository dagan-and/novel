import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "append_outline_footer.py"


class FakeRandom:
    def __init__(self):
        self.randint_values = [3, 8, 4, 9, 5, 10]
        self.choice_values = ["가자미구이", "병어구이", "고등어구이"]

    def randint(self, start, end):
        self.assert_range(start, end)
        return self.randint_values.pop(0)

    def choice(self, values):
        self.assert_choices(values)
        return self.choice_values.pop(0)

    @staticmethod
    def assert_range(start, end):
        if (start, end) != (1, 10):
            raise AssertionError("randint range must be 1~10")

    @staticmethod
    def assert_choices(values):
        if list(values) != ["가자미구이", "병어구이", "고등어구이"]:
            raise AssertionError("unexpected fish choices")


def load_module():
    spec = importlib.util.spec_from_file_location("append_outline_footer", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class AppendOutlineFooterTests(unittest.TestCase):
    def test_builds_random_footer_block_from_template(self):
        module = load_module()

        footer = module.build_footer_text(FakeRandom())

        self.assertEqual(
            footer,
            "**********\n물마심 3번\n밥먹음 8번\n[생선구이] 가자미구이",
        )

    def test_appends_random_footer_once_even_when_run_twice(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            outline = Path(temp_dir) / "sample.txt"
            outline.write_text("[성인씬 개요]\n\n도입:\n- 시작\n", encoding="utf-8")

            first = module.append_footer(outline, FakeRandom())
            second = module.append_footer(outline, FakeRandom())

            content = outline.read_text(encoding="utf-8")
            self.assertTrue(first.changed)
            self.assertFalse(second.changed)
            self.assertEqual(content.count("**********"), 1)
            self.assertEqual(content.count("물마심"), 1)
            self.assertEqual(content.count("밥먹음"), 1)
            self.assertEqual(content.count("[생선구이]"), 1)
            self.assertIn("<!-- outline-footer:", content)

    def test_applies_to_text_files_only(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            outline_dir = Path(temp_dir)
            (outline_dir / "a.txt").write_text("a\n", encoding="utf-8")
            (outline_dir / "b.md").write_text("b\n", encoding="utf-8")
            (outline_dir / ".DS_Store").write_bytes(b"ignored")

            result = module.append_to_outline_dir(outline_dir, FakeRandom())

            self.assertEqual(result.changed_count, 2)
            self.assertIn("**********", (outline_dir / "a.txt").read_text(encoding="utf-8"))
            self.assertIn("**********", (outline_dir / "b.md").read_text(encoding="utf-8"))
            self.assertEqual((outline_dir / ".DS_Store").read_bytes(), b"ignored")

    def test_cli_appends_fixed_footer_without_text_argument(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            outline = Path(temp_dir) / "sample.txt"
            outline.write_text("원문\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--outline-dir",
                    temp_dir,
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0)
            self.assertEqual(outline.read_text(encoding="utf-8").count("**********"), 1)


if __name__ == "__main__":
    unittest.main()
