"""Tests for load_rules input validation in mcp-server/server.py.

Validates that invalid --profile / --mode values fail loudly via the gateway
CLI, not silently return unstripped content.
"""

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


class TestProfileValidation(unittest.TestCase):
    def test_invalid_profile_planner_is_rejected(self):
        r = run("--profile", "planner", "--principle", "srp")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Invalid --profile 'planner'", r.stderr)
        self.assertIn("--mode", r.stderr)  # suggests the right flag

    def test_invalid_profile_code_review_is_rejected(self):
        for bad in ["synth-impl", "synth-fixes", "garbage", "Code", "REVIEW"]:
            with self.subTest(profile=bad):
                r = run("--profile", bad, "--principle", "srp")
                self.assertNotEqual(r.returncode, 0, f"{bad!r} should be rejected")
                self.assertIn(f"Invalid --profile '{bad}'", r.stderr)

    def test_valid_profile_code_works(self):
        r = run("--profile", "code", "--principle", "srp")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("SRP", r.stdout)

    def test_valid_profile_review_works(self):
        r = run("--profile", "review", "--principle", "srp")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("SRP", r.stdout)


class TestUnknownArgs(unittest.TestCase):
    def test_unknown_arg_is_rejected(self):
        r = run("--garbage", "foo", "--principle", "srp")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("unknown argument", r.stderr.lower())
        self.assertIn("garbage", r.stderr)

    def test_unknown_arg_lists_all_valid_args(self):
        r = run("--garbage", "foo", "--principle", "srp")
        self.assertNotEqual(r.returncode, 0)
        # All valid args for load_rules should be enumerated
        for arg in ["mode", "profile", "principle", "matched_tags", "exclude"]:
            self.assertIn(arg, r.stderr, f"valid arg '{arg}' not shown in help")

    def test_multiple_unknowns_are_listed(self):
        r = run("--foo", "1", "--bar", "2", "--mode", "code")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("foo", r.stderr)
        self.assertIn("bar", r.stderr)


class TestModeValidation(unittest.TestCase):
    def test_invalid_mode_is_rejected(self):
        r = run("--mode", "garbage", "--principle", "srp")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Invalid --mode 'garbage'", r.stderr)

    def test_valid_modes_all_work(self):
        for mode in ["code", "review", "planner", "synth-impl", "synth-fixes"]:
            with self.subTest(mode=mode):
                r = run("--mode", mode, "--principle", "srp")
                self.assertEqual(r.returncode, 0, f"{mode!r} failed: {r.stderr}")
                self.assertIn("SRP", r.stdout)

    def test_mode_strips_review_content_for_non_review(self):
        # Pick structured-concurrency since it has clear Detection blocks
        for mode in ["code", "planner", "synth-impl", "synth-fixes"]:
            with self.subTest(mode=mode):
                r = run("--mode", mode, "--principle", "structured-concurrency")
                self.assertEqual(r.returncode, 0)
                self.assertNotIn("**Detection:**", r.stdout,
                                 f"mode={mode} should strip Detection blocks")
                self.assertNotIn("Quantitative Metrics Summary", r.stdout,
                                 f"mode={mode} should strip Quantitative section")

    def test_review_mode_keeps_full_content(self):
        r = run("--mode", "review", "--principle", "structured-concurrency")
        self.assertEqual(r.returncode, 0)
        self.assertIn("**Detection:**", r.stdout)
        # Quantitative summary may or may not be in review/instructions.md depending
        # on principle structure; the key is Detection IS preserved


if __name__ == "__main__":
    unittest.main()
