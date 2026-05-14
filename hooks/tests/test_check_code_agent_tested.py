"""Tests for check_code_agent_tested.py"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS_DIR = str(Path(__file__).resolve().parents[1])
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

from check_code_agent_tested import _parse_transcript, _test_was_run

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


class TestParseTranscript(unittest.TestCase):
    def test_extracts_tool_names(self):
        path = _make_transcript([
            ("mcp__plugin_solid-coder_apple-build__build", {}),
            ("mcp__plugin_solid-coder_apple-build__test", {"skip_ui_tests": True}),
        ])
        names, cmds = _parse_transcript(path)
        self.assertIn("mcp__plugin_solid-coder_apple-build__test", names)
        self.assertIn("mcp__plugin_solid-coder_apple-build__build", names)
        self.assertEqual(cmds, [])

    def test_extracts_bash_commands(self):
        path = _make_transcript([
            ("Bash", {"command": "swift test --filter MyTests"}),
        ])
        names, cmds = _parse_transcript(path)
        self.assertIn("Bash", names)
        self.assertEqual(cmds, ["swift test --filter MyTests"])

    def test_missing_file_returns_empty(self):
        names, cmds = _parse_transcript("/nonexistent/path.jsonl")
        self.assertEqual(names, set())
        self.assertEqual(cmds, [])


class TestTestWasRun(unittest.TestCase):
    def test_mcp_test_tool_detected(self):
        self.assertTrue(_test_was_run({"mcp__plugin_solid-coder_apple-build__test"}, []))

    def test_xcodebuild_in_bash_detected(self):
        self.assertTrue(_test_was_run(set(), ["xcodebuild test -scheme MyApp"]))

    def test_swift_test_in_bash_detected(self):
        self.assertTrue(_test_was_run(set(), ["swift test"]))

    def test_pytest_in_bash_detected(self):
        self.assertTrue(_test_was_run(set(), ["pytest tests/"]))

    def test_unittest_in_bash_detected(self):
        self.assertTrue(_test_was_run(set(), ["python3 -m unittest discover"]))

    def test_no_test_returns_false(self):
        self.assertFalse(_test_was_run(
            {"mcp__plugin_solid-coder_apple-build__build", "Read", "Write"},
            ["ls", "git status"],
        ))


class TestMainHook(unittest.TestCase):
    def test_allows_when_test_tool_was_called(self):
        path = _make_transcript([
            ("mcp__plugin_solid-coder_apple-build__build", {}),
            ("mcp__plugin_solid-coder_apple-build__test", {"skip_ui_tests": True}),
        ])
        r = _run(_event(path))
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_blocks_when_no_test_was_run(self):
        path = _make_transcript([
            ("mcp__plugin_solid-coder_apple-build__build", {}),
            ("Write", {"file_path": "/foo/Bar.swift", "content": "..."}),
        ])
        r = _run(_event(path))
        self.assertEqual(r.returncode, 0)
        payload = json.loads(r.stdout)
        self.assertEqual(payload["decision"], "block")
        self.assertIn("Phase 5", payload["reason"])

    def test_allows_when_xcodebuild_test_in_bash(self):
        path = _make_transcript([
            ("Bash", {"command": "xcodebuild test -scheme MyApp -destination 'platform=macOS'"}),
        ])
        r = _run(_event(path))
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_passes_through_on_error_exit_reason(self):
        path = _make_transcript([("Write", {"file_path": "/foo/Bar.swift", "content": "..."})])
        r = _run(_event(path, exit_reason="error"))
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_passes_through_on_cancelled(self):
        path = _make_transcript([("Write", {"file_path": "/foo/Bar.swift", "content": "..."})])
        r = _run(_event(path, exit_reason="cancelled"))
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_malformed_stdin_passes_through(self):
        r = subprocess.run([sys.executable, SCRIPT], input="not json", capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
