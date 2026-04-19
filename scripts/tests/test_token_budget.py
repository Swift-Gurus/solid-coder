"""Tests for scripts/token-budget.py — hierarchical folder token accounting."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "token-budget.py"


def run(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, cwd=cwd,
    )


class TestTokenBudget(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        # Build a small fake tree:
        #   root/a/a1.md  (4 chars body → 1 tok)
        #   root/a/a2.md  (8 chars body → 2 tok)
        #   root/b/b1.md  (12 chars body → 3 tok)
        (self.root / "a").mkdir()
        (self.root / "b").mkdir()
        (self.root / "a" / "a1.md").write_text("abcd")
        (self.root / "a" / "a2.md").write_text("abcdefgh")
        (self.root / "b" / "b1.md").write_text("abcdefghijkl")

    def tearDown(self):
        self.tmp.cleanup()

    def test_runs_and_reports_total(self):
        r = run("--root", str(self.root))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Total", r.stdout)
        # Expected total: (4+8+12) / 4 = 6 tokens
        self.assertIn("6", r.stdout)

    def test_folders_contain_their_children(self):
        r = run("--root", str(self.root))
        # folder a = 1+2 = 3 tokens; folder b = 3 tokens
        self.assertIn("| &nbsp;&nbsp;&nbsp;&nbsp;📁 `a` | 3 |", r.stdout)
        self.assertIn("| &nbsp;&nbsp;&nbsp;&nbsp;📁 `b` | 3 |", r.stdout)

    def test_strips_frontmatter(self):
        f = self.root / "a" / "a3.md"
        # 10 chars of frontmatter + 8 chars of body
        f.write_text("---\nname: x\n---\nabcdefgh")
        r = run("--root", str(self.root))
        self.assertEqual(r.returncode, 0, r.stderr)
        # a3.md body is 8 chars → 2 tokens. Folder a = 1 + 2 + 2 = 5.
        self.assertIn("| &nbsp;&nbsp;&nbsp;&nbsp;📁 `a` | 5 |", r.stdout)

    def test_missing_root_exits_nonzero(self):
        r = run("--root", "/nonexistent/path/that/does/not/exist")
        self.assertNotEqual(r.returncode, 0)

    def test_writes_out_file(self):
        out = self.root / "report.md"
        r = run("--root", str(self.root), "--out", str(out))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(out.exists())
        content = out.read_text()
        self.assertIn("# Token Budget", content)
        self.assertIn("Total", content)

    def test_skips_hidden_and_cache_dirs(self):
        (self.root / ".hidden").mkdir()
        (self.root / ".hidden" / "secret.md").write_text("x" * 1000)
        (self.root / "__pycache__").mkdir()
        (self.root / "__pycache__" / "junk").write_text("x" * 1000)
        r = run("--root", str(self.root))
        self.assertNotIn(".hidden", r.stdout)
        self.assertNotIn("__pycache__", r.stdout)


if __name__ == "__main__":
    unittest.main()
