"""Tests for check_code_agent_tested.py"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS_DIR = str(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks")
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

from check_code_agent_tested import (
    _parse_transcript,
    _unit_test_files_written,
    _ui_test_files_written,
    _unit_test_was_run,
    _ui_test_was_run,
)

SCRIPT = str(Path(HOOKS_DIR) / "check_code_agent_tested.py")


def _make_transcript(tool_uses: list) -> str:
    """Write a minimal JSONL transcript and return its path."""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
    for name, inp in tool_uses:
        obj = {
            "type": "assistant",
            "message": {
                "content": [{"type": "tool_use", "name": name, "input": inp}]
            },
        }
        tmp.write(json.dumps(obj) + "\n")
    tmp.close()
    return tmp.name


def _run(event: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, SCRIPT],
        input=json.dumps(event),
        capture_output=True,
        text=True,
    )


def _event(transcript_path: str, exit_reason: str = "completed") -> dict:
    return {
        "hook_event_name": "SubagentStop",
        "agent_type": "solid-coder:code-agent",
        "exit_reason": exit_reason,
        "transcript_path": transcript_path,
    }


# ---------------------------------------------------------------------------
# _parse_transcript
# ---------------------------------------------------------------------------

class TestParseTranscript(unittest.TestCase):
    def test_extracts_tool_names_and_mcp_test_calls(self):
        path = _make_transcript([
            ("mcp__plugin_solid-coder_apple-build__test", {"skip_ui_tests": True}),
        ])
        names, cmds, test_calls, written = _parse_transcript(path)
        self.assertEqual(len(test_calls), 1)
        self.assertEqual(test_calls[0]["skip_ui_tests"], True)

    def test_extracts_written_paths(self):
        path = _make_transcript([
            ("Write", {"file_path": "/proj/FooTests.swift", "content": "..."}),
            ("Edit", {"file_path": "/proj/Bar.swift", "old_string": "x", "new_string": "y"}),
        ])
        _, _, _, written = _parse_transcript(path)
        self.assertIn("/proj/FooTests.swift", written)
        self.assertIn("/proj/Bar.swift", written)

    def test_missing_file_returns_empty(self):
        names, cmds, test_calls, written = _parse_transcript("/nonexistent/path.jsonl")
        self.assertEqual(names, set())
        self.assertEqual(written, [])


# ---------------------------------------------------------------------------
# _unit_test_files_written
# ---------------------------------------------------------------------------

class TestUnitTestFilesWritten(unittest.TestCase):
    def test_detects_swift_test_file(self):
        self.assertTrue(_unit_test_files_written(["/proj/FooTests.swift"]))

    def test_detects_spec_file(self):
        self.assertTrue(_unit_test_files_written(["/proj/FooSpec.swift"]))

    def test_detects_test_in_path(self):
        self.assertTrue(_unit_test_files_written(["/proj/Tests/FooTest.swift"]))

    def test_does_not_detect_uitest_file(self):
        # UITest files are handled separately
        self.assertFalse(_unit_test_files_written(["/proj/FooUITests.swift"]))

    def test_does_not_detect_production_file(self):
        self.assertFalse(_unit_test_files_written(["/proj/Foo.swift", "/proj/Bar.swift"]))

    def test_empty_paths_returns_false(self):
        self.assertFalse(_unit_test_files_written([]))


# ---------------------------------------------------------------------------
# _ui_test_files_written
# ---------------------------------------------------------------------------

class TestUITestFilesWritten(unittest.TestCase):
    def test_detects_uitest_file(self):
        self.assertTrue(_ui_test_files_written(["/proj/AppUITests.swift"]))

    def test_detects_ui_underscore_test(self):
        self.assertTrue(_ui_test_files_written(["/proj/App_UI_Test.swift"]))

    def test_does_not_detect_unit_test_file(self):
        self.assertFalse(_ui_test_files_written(["/proj/FooTests.swift"]))

    def test_empty_returns_false(self):
        self.assertFalse(_ui_test_files_written([]))


# ---------------------------------------------------------------------------
# _unit_test_was_run / _ui_test_was_run (unchanged logic)
# ---------------------------------------------------------------------------

class TestUnitTestWasRun(unittest.TestCase):
    def test_mcp_test_without_skip_unit_counts(self):
        self.assertTrue(_unit_test_was_run(set(), [], [{"skip_unit_tests": False}]))

    def test_mcp_test_with_skip_unit_does_not_count(self):
        self.assertFalse(_unit_test_was_run(set(), [], [{"skip_unit_tests": True}]))

    def test_xcodebuild_test_counts(self):
        self.assertTrue(_unit_test_was_run(set(), ["xcodebuild test -scheme MyApp"], []))

    def test_xcodebuild_build_only_does_not_count(self):
        self.assertFalse(_unit_test_was_run(set(), ["xcodebuild build -scheme MyApp"], []))

    def test_no_test_returns_false(self):
        self.assertFalse(_unit_test_was_run({"Read", "Write"}, ["ls"], []))


# ---------------------------------------------------------------------------
# Integration — main()
# ---------------------------------------------------------------------------

class TestMainHook(unittest.TestCase):
    def test_no_test_files_written_passes_through(self):
        # Agent wrote only production code — hook should NOT block
        path = _make_transcript([
            ("Write", {"file_path": "/proj/Calculator.swift", "content": "..."}),
            ("mcp__plugin_solid-coder_apple-build__build", {}),
        ])
        r = _run(_event(path))
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_wrote_tests_but_no_run_blocks(self):
        # Agent wrote FooTests.swift but never ran tests — BLOCK
        path = _make_transcript([
            ("Write", {"file_path": "/proj/FooTests.swift", "content": "..."}),
            ("mcp__plugin_solid-coder_apple-build__build", {}),
        ])
        r = _run(_event(path))
        payload = json.loads(r.stdout)
        self.assertEqual(payload["decision"], "block")
        self.assertIn("Phase 5", payload["reason"])

    def test_wrote_tests_and_ran_them_passes(self):
        # Agent wrote tests AND ran them — allow
        path = _make_transcript([
            ("Write", {"file_path": "/proj/FooTests.swift", "content": "..."}),
            ("mcp__plugin_solid-coder_apple-build__test", {}),
        ])
        r = _run(_event(path))
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_wrote_uitests_but_only_ran_unit_blocks(self):
        # Wrote UITests.swift, ran unit tests only (skip_ui_tests=True) — BLOCK
        path = _make_transcript([
            ("Write", {"file_path": "/proj/AppUITests.swift", "content": "..."}),
            ("mcp__plugin_solid-coder_apple-build__test", {"skip_ui_tests": True}),
        ])
        r = _run(_event(path))
        payload = json.loads(r.stdout)
        self.assertEqual(payload["decision"], "block")

    def test_wrote_uitests_and_ran_uitests_passes(self):
        # Wrote UITests, ran UI tests — allow
        path = _make_transcript([
            ("Write", {"file_path": "/proj/AppUITests.swift", "content": "..."}),
            ("mcp__plugin_solid-coder_apple-build__test", {"skip_unit_tests": True}),
        ])
        r = _run(_event(path))
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_xcodebuild_build_only_still_blocks(self):
        # Agent wrote tests, ran xcodebuild build (not test) — BLOCK
        path = _make_transcript([
            ("Write", {"file_path": "/proj/FooTests.swift", "content": "..."}),
            ("Bash", {"command": "xcodebuild build -scheme MyApp"}),
        ])
        r = _run(_event(path))
        payload = json.loads(r.stdout)
        self.assertEqual(payload["decision"], "block")

    def test_passes_through_on_error_exit_reason(self):
        path = _make_transcript([("Write", {"file_path": "/proj/FooTests.swift", "content": "..."})])
        r = _run(_event(path, exit_reason="error"))
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_passes_through_on_cancelled(self):
        path = _make_transcript([("Write", {"file_path": "/proj/FooTests.swift", "content": "..."})])
        r = _run(_event(path, exit_reason="cancelled"))
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_malformed_stdin_passes_through(self):
        r = subprocess.run([sys.executable, SCRIPT], input="not json",
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
