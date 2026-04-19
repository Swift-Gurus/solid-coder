"""Tests for scripts/regen-token-docs.py — hook-facing wrapper."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "regen-token-docs.py"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_hook():
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True, text=True, cwd=PROJECT_ROOT,
    )


class TestHookOutput(unittest.TestCase):
    def test_produces_valid_json(self):
        r = run_hook()
        self.assertEqual(r.returncode, 0, r.stderr)
        payload = json.loads(r.stdout)
        self.assertIsInstance(payload, dict)

    def test_payload_includes_hook_specific_output(self):
        r = run_hook()
        payload = json.loads(r.stdout)
        self.assertIn("hookSpecificOutput", payload)
        hso = payload["hookSpecificOutput"]
        self.assertEqual(hso.get("hookEventName"), "PostToolUse")
        self.assertIn("additionalContext", hso)

    def test_context_mentions_modes(self):
        r = run_hook()
        payload = json.loads(r.stdout)
        ctx = payload["hookSpecificOutput"]["additionalContext"]
        for mode in ["code", "review", "planner", "synth-impl", "synth-fixes"]:
            self.assertIn(mode, ctx, f"mode '{mode}' missing from hook output")

    def test_context_reports_numbers(self):
        r = run_hook()
        payload = json.loads(r.stdout)
        ctx = payload["hookSpecificOutput"]["additionalContext"]
        # expect "max " followed by digits
        import re
        self.assertTrue(re.search(r"max\s+[\d,]+", ctx),
                        f"expected 'max <number>' in:\n{ctx}")

    def test_regenerates_both_docs(self):
        budget = PROJECT_ROOT / ".claude" / "docs" / "token-budget.md"
        cost = PROJECT_ROOT / ".claude" / "docs" / "token-cost-by-mode.md"
        run_hook()
        self.assertTrue(budget.exists())
        self.assertTrue(cost.exists())


if __name__ == "__main__":
    unittest.main()
