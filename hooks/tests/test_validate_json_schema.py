"""Subprocess tests for validate_json_schema.py (PreToolUse hook).

Tests invoke the script via its CLI contract — stdin = hook event JSON,
stdout/exit-code = hook decision.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parent.parent / "validate_json_schema.py"
PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def _run(payload: dict) -> tuple[int, str, str]:
    env = os.environ.copy()
    env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _is_blocked(stdout: str) -> bool:
    if not stdout.strip():
        return False
    try:
        out = json.loads(stdout)
    except json.JSONDecodeError:
        return False
    spec = out.get("hookSpecificOutput") or {}
    return spec.get("permissionDecision") == "deny"


def _block_reason(stdout: str) -> str:
    return json.loads(stdout)["hookSpecificOutput"]["permissionDecisionReason"]


_VALID_ARCH = {
    "spec_number": "SPEC-041",
    "spec_summary": "summary",
    "components": [],
    "wiring": [],
    "composition_root": "",
}

_VALID_VALIDATION = {
    "spec_number": "SPEC-041",
    "components": [],
    "summary": {"create": 0, "reuse": 0, "adjust": 0, "conflict": 0},
}

_VALID_PLAN = {
    "spec_number": "SPEC-041",
    "spec_summary": "summary",
    "plan_items": [],
    "reconciliation_decisions": [],
    "summary": {"create": 0, "modify": 0, "reuse": 0},
}


def _payload(file_path: str, content, tool: str = "Write") -> dict:
    body = content if isinstance(content, str) else json.dumps(content)
    return {
        "tool_name": tool,
        "tool_input": {"file_path": file_path, "content": body},
    }


class ValidateJsonSchemaCLITests(unittest.TestCase):
    def test_non_json_file_is_allowed(self):
        rc, stdout, _ = _run(_payload("/tmp/random.txt", "hello"))
        self.assertEqual(rc, 0)
        self.assertFalse(_is_blocked(stdout))

    def test_unknown_json_filename_is_allowed(self):
        rc, stdout, _ = _run(_payload("/tmp/random.json", "{}"))
        self.assertEqual(rc, 0)
        self.assertFalse(_is_blocked(stdout))

    def test_non_write_tool_is_allowed(self):
        rc, stdout, _ = _run(_payload("/tmp/arch.json", _VALID_ARCH, tool="Edit"))
        self.assertEqual(rc, 0)
        self.assertFalse(_is_blocked(stdout))

    def test_valid_arch_is_allowed(self):
        rc, stdout, _ = _run(_payload("/tmp/arch.json", _VALID_ARCH))
        self.assertEqual(rc, 0)
        self.assertFalse(_is_blocked(stdout))

    def test_valid_validation_is_allowed(self):
        rc, stdout, _ = _run(_payload("/tmp/validation.json", _VALID_VALIDATION))
        self.assertEqual(rc, 0)
        self.assertFalse(_is_blocked(stdout))

    def test_valid_plan_is_allowed(self):
        rc, stdout, _ = _run(_payload("/tmp/implementation-plan.json", _VALID_PLAN))
        self.assertEqual(rc, 0)
        self.assertFalse(_is_blocked(stdout))

    def test_arch_missing_required_field_is_blocked(self):
        bad = dict(_VALID_ARCH)
        del bad["spec_summary"]
        rc, stdout, _ = _run(_payload("/tmp/arch.json", bad))
        self.assertEqual(rc, 0)
        self.assertTrue(_is_blocked(stdout))
        self.assertIn("spec_summary", _block_reason(stdout))

    def test_validation_missing_summary_is_blocked(self):
        bad = dict(_VALID_VALIDATION)
        del bad["summary"]
        rc, stdout, _ = _run(_payload("/tmp/validation.json", bad))
        self.assertEqual(rc, 0)
        self.assertTrue(_is_blocked(stdout))
        self.assertIn("summary", _block_reason(stdout))

    def test_plan_missing_reconciliation_decisions_is_blocked(self):
        bad = dict(_VALID_PLAN)
        del bad["reconciliation_decisions"]
        rc, stdout, _ = _run(_payload("/tmp/implementation-plan.json", bad))
        self.assertEqual(rc, 0)
        self.assertTrue(_is_blocked(stdout))
        self.assertIn("reconciliation_decisions", _block_reason(stdout))

    def test_invalid_json_content_is_blocked(self):
        rc, stdout, _ = _run(_payload("/tmp/arch.json", "{not: valid json"))
        self.assertEqual(rc, 0)
        self.assertTrue(_is_blocked(stdout))
        self.assertIn("invalid JSON", _block_reason(stdout))

    def test_malformed_hook_input_fails_open(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input="not json",
            capture_output=True,
            text=True,
            env={**os.environ, "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT)},
        )
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "")

    def test_block_reason_includes_filename_and_count(self):
        bad = {"spec_summary": "x"}  # missing 3 required fields
        rc, stdout, _ = _run(_payload("/tmp/arch.json", bad))
        self.assertEqual(rc, 0)
        self.assertTrue(_is_blocked(stdout))
        reason = _block_reason(stdout)
        self.assertIn("arch.json", reason)
        self.assertIn("error(s)", reason)


if __name__ == "__main__":
    unittest.main()
