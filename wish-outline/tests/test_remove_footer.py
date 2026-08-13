import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
SCRIPT_PATH = TOOLS_DIR / "remove_footer.py"
APPEND_SCRIPT_PATH = TOOLS_DIR / "append_footer.py"


def load_module():
    spec = importlib.util.spec_from_file_location("remove_footer", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_append_module():
    spec = importlib.util.spec_from_file_location("append_footer", APPEND_SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RemoveOutlineFooterTests(unittest.TestCase):
    def test_removes_outline_footer_marker_and_everything_after_it(self):
        module = load_module()
        append_module = load_append_module()

        marker = append_module.footer_marker(append_module.FOOTER_MARKER_TEXT)
        with tempfile.TemporaryDirectory() as temp_dir:
            outline = Path(temp_dir) / "sample.txt"
            outline.write_text(
                f"원문 1\n원문 2\n\n{marker}\n**********\n삭제될 내용\n",
                encoding="utf-8",
            )

            result = module.remove_footer(outline)

            self.assertTrue(result.changed)
            self.assertEqual(outline.read_text(encoding="utf-8"), "원문 1\n원문 2\n")

    def test_leaves_files_without_outline_footer_unchanged(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            outline = Path(temp_dir) / "sample.txt"
            outline.write_text("원문\n**********\n일반 내용\n", encoding="utf-8")

            result = module.remove_footer(outline)

            self.assertFalse(result.changed)
            self.assertEqual(outline.read_text(encoding="utf-8"), "원문\n**********\n일반 내용\n")

    def test_applies_to_text_files_only(self):
        module = load_module()
        append_module = load_append_module()

        marker = append_module.footer_marker(append_module.FOOTER_MARKER_TEXT)
        with tempfile.TemporaryDirectory() as temp_dir:
            outline_dir = Path(temp_dir)
            (outline_dir / "a.txt").write_text(f"a\n{marker}\nfooter\n", encoding="utf-8")
            (outline_dir / "b.log").write_text(f"b\n{marker}\nfooter\n", encoding="utf-8")

            result = module.remove_from_outline_dir(outline_dir)

            self.assertEqual(result.scanned_count, 1)
            self.assertEqual(result.changed_count, 1)
            self.assertEqual((outline_dir / "a.txt").read_text(encoding="utf-8"), "a\n")
            self.assertIn(marker, (outline_dir / "b.log").read_text(encoding="utf-8"))

    def test_cli_removes_footer_from_default_outline_dir(self):
        append_module = load_append_module()
        marker = append_module.footer_marker(append_module.FOOTER_MARKER_TEXT)

        with tempfile.TemporaryDirectory() as temp_dir:
            outline_dir = Path(temp_dir) / "outlines"
            outline_dir.mkdir()
            outline = outline_dir / "sample.txt"
            outline.write_text(f"원문\n{marker}\nfooter\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--outline-dir",
                    str(outline_dir),
                ],
                cwd=temp_dir,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0)
            self.assertEqual(outline.read_text(encoding="utf-8"), "원문\n")
            self.assertIn("Changed: 1", completed.stdout)


if __name__ == "__main__":
    unittest.main()
