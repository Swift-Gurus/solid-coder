"""Gateway CLI tests for load_rules mode/arg validation and content contracts."""

import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GATEWAY = PROJECT_ROOT / "mcp-server" / "gateway.py"


def run(*args):
    return subprocess.run(
        [sys.executable, str(GATEWAY), "load_rules", *args],
        capture_output=True, text=True, cwd=PROJECT_ROOT,
    )


class TestUnknownArgs(unittest.TestCase):
    def test_unknown_arg_is_rejected(self):
        r = run("--garbage", "foo", "--principle", "srp")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("unknown argument", r.stderr.lower())
        self.assertIn("garbage", r.stderr)

    def test_unknown_arg_lists_all_valid_args(self):
        r = run("--garbage", "foo", "--principle", "srp")
        self.assertNotEqual(r.returncode, 0)
        for arg in ["mode", "principle", "matched_tags"]:
            self.assertIn(arg, r.stderr, f"valid arg '{arg}' not shown in help")

    def test_multiple_unknowns_are_listed(self):
        r = run("--foo", "1", "--bar", "2", "--mode", "code")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("foo", r.stderr)
        self.assertIn("bar", r.stderr)

    def test_profile_flag_rejected(self):
        r = run("--profile", "code", "--principle", "srp")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("profile", r.stderr)


class TestModeValidation(unittest.TestCase):
    def test_invalid_mode_is_rejected(self):
        r = run("--mode", "garbage", "--principle", "srp")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("garbage", r.stderr)

    def test_valid_modes_all_return_content(self):
        for mode in ["code", "review", "planner", "synth-impl", "synth-fixes"]:
            with self.subTest(mode=mode):
                r = run("--mode", mode, "--principle", "srp")
                self.assertEqual(r.returncode, 0, f"{mode!r} failed: {r.stderr}")
                self.assertGreater(len(r.stdout.strip()), 100, f"{mode}: output too short")
                self.assertIn("SRP", r.stdout)

    def test_review_mode_includes_severity_bands(self):
        r = run("--mode", "review", "--principle", "srp")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("<severity-bands", r.stdout)

    def test_non_review_modes_exclude_severity_bands(self):
        for mode in ["code", "planner", "synth-impl", "synth-fixes"]:
            with self.subTest(mode=mode):
                r = run("--mode", mode, "--principle", "srp")
                self.assertEqual(r.returncode, 0)
                self.assertNotIn("<severity-bands", r.stdout,
                                 f"{mode}: must not include severity-bands")

    def test_review_mode_includes_review_instructions(self):
        r = run("--mode", "review", "--principle", "srp")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("review/instructions.md", r.stdout)

    def test_non_review_modes_exclude_review_instructions(self):
        for mode in ["code", "planner", "synth-impl", "synth-fixes"]:
            with self.subTest(mode=mode):
                r = run("--mode", mode, "--principle", "srp")
                self.assertEqual(r.returncode, 0)
                self.assertNotIn("review/instructions.md", r.stdout,
                                 f"{mode}: must not include review/instructions.md")


if __name__ == "__main__":
    unittest.main()
