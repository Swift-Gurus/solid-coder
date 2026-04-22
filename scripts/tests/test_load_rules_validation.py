"""Tests for load_rules input validation in mcp-server/server.py.

Validates that invalid --profile / --mode values fail loudly via the gateway
CLI, and that valid inputs return paths_to_load JSON.
"""

import json
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


def paths(r):
    return json.loads(r.stdout)["paths_to_load"]


class TestProfileValidation(unittest.TestCase):
    def test_invalid_profile_planner_is_rejected(self):
        r = run("--profile", "planner", "--principle", "srp")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Invalid --profile 'planner'", r.stderr)
        self.assertIn("--mode", r.stderr)

    def test_invalid_profile_code_review_is_rejected(self):
        for bad in ["synth-impl", "synth-fixes", "garbage", "Code", "REVIEW"]:
            with self.subTest(profile=bad):
                r = run("--profile", bad, "--principle", "srp")
                self.assertNotEqual(r.returncode, 0, f"{bad!r} should be rejected")
                self.assertIn(f"Invalid --profile '{bad}'", r.stderr)

    def test_valid_profile_code_works(self):
        r = run("--profile", "code", "--principle", "srp")
        self.assertEqual(r.returncode, 0, r.stderr)
        ps = paths(r)
        self.assertTrue(any("SRP" in p for p in ps))

    def test_valid_profile_review_works(self):
        r = run("--profile", "review", "--principle", "srp")
        self.assertEqual(r.returncode, 0, r.stderr)
        ps = paths(r)
        self.assertTrue(any("SRP" in p for p in ps))


class TestUnknownArgs(unittest.TestCase):
    def test_unknown_arg_is_rejected(self):
        r = run("--garbage", "foo", "--principle", "srp")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("unknown argument", r.stderr.lower())
        self.assertIn("garbage", r.stderr)

    def test_unknown_arg_lists_all_valid_args(self):
        r = run("--garbage", "foo", "--principle", "srp")
        self.assertNotEqual(r.returncode, 0)
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
                ps = paths(r)
                self.assertTrue(any("SRP" in p for p in ps), f"{mode}: no SRP path")

    def test_review_mode_includes_review_instructions(self):
        r = run("--mode", "review", "--principle", "srp")
        self.assertEqual(r.returncode, 0, r.stderr)
        ps = paths(r)
        self.assertTrue(any("review" in p and "instructions.md" in p for p in ps),
                        "review mode must include review/instructions.md")

    def test_non_review_modes_exclude_review_instructions(self):
        for mode in ["code", "planner", "synth-impl", "synth-fixes"]:
            with self.subTest(mode=mode):
                r = run("--mode", mode, "--principle", "srp")
                self.assertEqual(r.returncode, 0)
                ps = paths(r)
                self.assertFalse(any("review/instructions.md" in p for p in ps),
                                 f"{mode}: must not include review/instructions.md")

    def test_all_returned_paths_exist(self):
        for mode in ["code", "review", "planner", "synth-impl", "synth-fixes"]:
            with self.subTest(mode=mode):
                r = run("--mode", mode, "--principle", "srp")
                self.assertEqual(r.returncode, 0)
                for p in paths(r):
                    self.assertTrue(Path(p).is_file(), f"{mode}: path missing: {p}")


if __name__ == "__main__":
    unittest.main()
