"""Tests for pre_write_gate.py"""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

HOOKS_DIR = str(Path(__file__).resolve().parents[1])
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

import pre_write_gate as gate

LONG_SWIFT = "import Foundation\n\nfinal class Foo {\n" + "    func bar() {}\n" * 35 + "}\n"
LONG_SWIFT_WITH_FRONTMATTER = (
    "/**\n solid-name: Foo\n solid-category: service\n"
    " solid-description: Loads data using URLSession.shared.\n */\n"
    "final class Foo {\n" + "    func bar() {}\n" * 35 + "}\n"
)
CORRECTED_FRONTMATTER = (
    "/**\n solid-name: Foo\n solid-category: service\n"
    " solid-description: Coordinates asynchronous data retrieval.\n */\n"
    "final class Foo {\n" + "    func bar() {}\n" * 35 + "}\n"
)
SHORT_SWIFT = "final class Foo {\n    func bar() {}\n}\n"
VIOLATIONS = [{"principle": "SRP", "issue": "Two concerns.", "fix": "Extract."}]


def _call_main(stdin_json: dict) -> tuple:
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    code = 0
    with patch("sys.stdin", io.StringIO(json.dumps(stdin_json))):
        with redirect_stdout(buf):
            try:
                gate.main()
            except SystemExit as e:
                code = e.code or 0
    return code, buf.getvalue()


def _event(tool: str, path: str, content: str) -> dict:
    key = "content" if tool == "Write" else "new_string"
    inp = {"file_path": path, key: content}
    if tool == "Edit":
        inp["old_string"] = "old"
    return {"tool_name": tool, "tool_input": inp, "session_id": "test"}


class TestGateSkipConditions(unittest.TestCase):
    def test_non_swift_allows_without_checks(self):
        with patch("pre_write_gate._run_frontmatter") as fm, \
             patch("pre_write_gate._run_health") as hc:
            code, out = _call_main(_event("Write", "/src/Foo.py", LONG_SWIFT))
        fm.assert_not_called()
        hc.assert_not_called()
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_new_swift_file_runs_health_check(self):
        """Health check always runs for new .swift files regardless of size."""
        with patch("pre_write_gate._run_frontmatter", return_value=SHORT_SWIFT), \
             patch("pre_write_gate._run_health", return_value=[]) as hc:
            code, out = _call_main(_event("Write", "/src/Foo.swift", SHORT_SWIFT))
        hc.assert_called_once()

    def test_test_file_runs_health_check(self):
        """Test files are no longer excluded — unit testing rules apply."""
        with patch("pre_write_gate._run_frontmatter", return_value=LONG_SWIFT), \
             patch("pre_write_gate._run_health", return_value=[]) as hc:
            code, out = _call_main(_event("Write", "/src/FooTests.swift", LONG_SWIFT))
        hc.assert_called_once()

    def test_read_tool_allows_immediately(self):
        with patch("pre_write_gate._run_frontmatter") as fm:
            code, _ = _call_main({"tool_name": "Read", "tool_input": {"file_path": "/src/Foo.swift"}, "session_id": "s"})
        fm.assert_not_called()
        self.assertEqual(code, 0)


class TestGateDecisions(unittest.TestCase):
    def test_both_clean_allows(self):
        with patch("pre_write_gate._run_frontmatter", return_value=LONG_SWIFT_WITH_FRONTMATTER), \
             patch("pre_write_gate._run_health", return_value=[]):
            code, out = _call_main(_event("Write", "/src/Foo.swift", LONG_SWIFT_WITH_FRONTMATTER))
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_health_violations_blocks_without_running_frontmatter(self):
        """Health check blocks immediately — frontmatter never runs."""
        with patch("pre_write_gate._run_frontmatter") as fm, \
             patch("pre_write_gate._run_health", return_value=VIOLATIONS):
            code, out = _call_main(_event("Write", "/src/Foo.swift", LONG_SWIFT))
        payload = json.loads(out)
        h = payload["hookSpecificOutput"]
        self.assertEqual(h["permissionDecision"], "deny")
        self.assertIn("SRP", h["permissionDecisionReason"])
        self.assertIn("The file was NOT written", h["permissionDecisionReason"])
        fm.assert_not_called()

    def test_frontmatter_correction_only_runs_when_health_passes(self):
        """Frontmatter runs after health check returns clean."""
        with patch("pre_write_gate._run_frontmatter", return_value=CORRECTED_FRONTMATTER), \
             patch("pre_write_gate._run_health", return_value=[]):
            code, out = _call_main(_event("Write", "/src/Foo.swift", LONG_SWIFT_WITH_FRONTMATTER))
        payload = json.loads(out)
        h = payload["hookSpecificOutput"]
        self.assertEqual(h["permissionDecision"], "allow")
        self.assertEqual(h["updatedInput"]["content"], CORRECTED_FRONTMATTER)

    def test_deny_has_no_frontmatter_blocks(self):
        """On deny, frontmatter is never run so no corrected blocks in reason."""
        with patch("pre_write_gate._run_health", return_value=VIOLATIONS):
            code, out = _call_main(_event("Write", "/src/Foo.swift", LONG_SWIFT))
        h = json.loads(out)["hookSpecificOutput"]
        self.assertEqual(h["permissionDecision"], "deny")
        self.assertNotIn("corrected frontmatter", h["permissionDecisionReason"])

    def test_frontmatter_error_fails_open(self):
        with patch("pre_write_gate._run_frontmatter", return_value=None), \
             patch("pre_write_gate._run_health", return_value=[]):
            code, out = _call_main(_event("Write", "/src/Foo.swift", LONG_SWIFT_WITH_FRONTMATTER))
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_health_error_fails_open(self):
        with patch("pre_write_gate._run_frontmatter", return_value=LONG_SWIFT), \
             patch("pre_write_gate._run_health", return_value=None):
            code, out = _call_main(_event("Write", "/src/Foo.swift", LONG_SWIFT))
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_edit_tool_uses_new_string_key(self):
        with patch("pre_write_gate._run_frontmatter", return_value=CORRECTED_FRONTMATTER), \
             patch("pre_write_gate._run_health", return_value=[]):
            code, out = _call_main(_event("Edit", "/src/Foo.swift", LONG_SWIFT_WITH_FRONTMATTER))
        payload = json.loads(out)
        updated = payload["hookSpecificOutput"]["updatedInput"]
        self.assertIn("new_string", updated)
        self.assertEqual(updated["new_string"], CORRECTED_FRONTMATTER)

    def test_no_frontmatter_health_clean_allows(self):
        """No solid-description means frontmatter correction is skipped.
        Health check still runs; if clean it allows silently."""
        with patch("pre_write_gate._run_frontmatter") as fm, \
             patch("pre_write_gate._run_health", return_value=[]) as hc:
            code, out = _call_main(_event("Write", "/src/Foo.swift", SHORT_SWIFT))
        hc.assert_called_once()
        fm.assert_not_called()  # no solid-description in SHORT_SWIFT
        self.assertEqual(out, "")

    def test_malformed_stdin_allows(self):
        import io
        with patch("sys.stdin", io.StringIO("not json")):
            try:
                gate.main()
            except SystemExit as e:
                self.assertEqual(e.code or 0, 0)


if __name__ == "__main__":
    unittest.main()
