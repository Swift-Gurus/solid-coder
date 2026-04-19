"""Tests for the --output-format flag on gateway.py load_rules.

Formatters:
  - md (default) — readable text, used by CLI / skills
  - hook-json    — SubagentStart hook response JSON with
                   hookSpecificOutput.additionalContext populated
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


class TestDefaultFormat(unittest.TestCase):
    def test_default_is_md(self):
        """No --output-format flag → readable text (backward compatible)."""
        r = run("--mode", "planner", "--principle", "srp")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("SRP", r.stdout)
        self.assertIn("ACTIVE PRINCIPLES", r.stdout)
        # Not JSON
        with self.assertRaises(json.JSONDecodeError):
            json.loads(r.stdout)


class TestMdFormat(unittest.TestCase):
    def test_explicit_md_matches_default(self):
        default = run("--mode", "planner", "--principle", "srp")
        explicit = run("--mode", "planner", "--principle", "srp",
                       "--output-format", "md")
        self.assertEqual(explicit.returncode, 0, explicit.stderr)
        self.assertEqual(default.stdout, explicit.stdout)


class TestHookJsonFormat(unittest.TestCase):
    def test_hook_json_is_valid_json(self):
        r = run("--mode", "planner", "--principle", "srp",
                "--output-format", "hook-json")
        self.assertEqual(r.returncode, 0, r.stderr)
        # Must be parseable JSON
        parsed = json.loads(r.stdout)
        self.assertIsInstance(parsed, dict)

    def test_hook_json_has_expected_shape(self):
        r = run("--mode", "planner", "--principle", "srp",
                "--output-format", "hook-json")
        parsed = json.loads(r.stdout)
        self.assertIn("hookSpecificOutput", parsed)
        hso = parsed["hookSpecificOutput"]
        self.assertEqual(hso.get("hookEventName"), "SubagentStart")
        self.assertIn("additionalContext", hso)
        self.assertIsInstance(hso["additionalContext"], str)

    def test_hook_json_additional_context_contains_rules(self):
        """The injected context must carry the same rule content as md mode."""
        r = run("--mode", "planner", "--principle", "srp",
                "--output-format", "hook-json")
        parsed = json.loads(r.stdout)
        ctx = parsed["hookSpecificOutput"]["additionalContext"]
        self.assertIn("SRP", ctx)
        self.assertIn("ACTIVE PRINCIPLES", ctx)

    def test_hook_json_context_equals_md_output(self):
        """hook-json embeds the exact md rendering — no duplication or drift."""
        md = run("--mode", "planner", "--principle", "srp",
                 "--output-format", "md")
        hj = run("--mode", "planner", "--principle", "srp",
                 "--output-format", "hook-json")
        parsed = json.loads(hj.stdout)
        self.assertEqual(parsed["hookSpecificOutput"]["additionalContext"],
                         md.stdout.rstrip("\n"))


class TestInvalidFormat(unittest.TestCase):
    def test_invalid_format_is_rejected(self):
        r = run("--mode", "planner", "--principle", "srp",
                "--output-format", "xml")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("invalid --output-format", r.stderr.lower())

    def test_invalid_format_lists_valid_options(self):
        r = run("--mode", "planner", "--principle", "srp",
                "--output-format", "garbage")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("md", r.stderr)
        self.assertIn("hook-json", r.stderr)


if __name__ == "__main__":
    unittest.main()
