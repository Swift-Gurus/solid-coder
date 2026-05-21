"""Tests for pre_write_gate.py"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

import pre_write_gate as gate
import test_utils
from test_utils import parse_hook_output

LONG_SWIFT = test_utils.LONG_SWIFT
SHORT_SWIFT = test_utils.SHORT_SWIFT

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
VIOLATIONS = [{"principle": "SRP", "issue": "Two concerns.", "fix": "Extract."}]


def _call_main(stdin_input) -> tuple:
    return test_utils.call_main(stdin_input, gate.main)


_event = test_utils.event


class TestGateSkipConditions(unittest.TestCase):
    def test_non_swift_allows_without_checks(self):
        with patch("pre_write_gate._run_frontmatter") as fm, \
             patch("pre_write_gate._run_health") as hc:
            code, out = _call_main(_event("Write", "/src/Foo.kt", LONG_SWIFT))
        fm.assert_not_called()
        hc.assert_not_called()
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_new_swift_file_runs_health_check(self):
        """Health check always runs for new .swift files regardless of size."""
        with patch("pre_write_gate._run_frontmatter", return_value=SHORT_SWIFT), \
             patch("pre_write_gate._run_health", return_value=[]) as hc:
            _call_main(_event("Write", "/src/Foo.swift", SHORT_SWIFT))
        hc.assert_called_once()

    def test_test_file_runs_health_check(self):
        """Test files are no longer excluded — unit testing rules apply."""
        with patch("pre_write_gate._run_frontmatter", return_value=LONG_SWIFT), \
             patch("pre_write_gate._run_health", return_value=[]) as hc:
            _call_main(_event("Write", "/src/FooTests.swift", LONG_SWIFT))
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
        """Health violations deny the write — _run_frontmatter is never reached.

        Uses content WITH solid-description so run_frontmatter=True; the only
        reason fm is not called is that _deny(violations) -> sys.exit(0) exits
        the process before Step 2 runs.
        """
        with patch("pre_write_gate._run_frontmatter") as fm, \
             patch("pre_write_gate._run_health", return_value=VIOLATIONS):
            code, out = _call_main(_event("Write", "/src/Foo.swift", LONG_SWIFT_WITH_FRONTMATTER))
        h = parse_hook_output(out)
        self.assertEqual(h["permissionDecision"], "deny")
        self.assertIn("SRP", h["permissionDecisionReason"])
        self.assertIn("The file was NOT written", h["permissionDecisionReason"])
        fm.assert_not_called()

    def test_frontmatter_correction_only_runs_when_health_passes(self):
        """Frontmatter runs after health check returns clean."""
        with patch("pre_write_gate._run_frontmatter", return_value=CORRECTED_FRONTMATTER) as fm, \
             patch("pre_write_gate._run_health", return_value=[]):
            code, out = _call_main(_event("Write", "/src/Foo.swift", LONG_SWIFT_WITH_FRONTMATTER))
        h = parse_hook_output(out)
        self.assertEqual(h["permissionDecision"], "allow")
        self.assertEqual(h["updatedInput"]["content"], CORRECTED_FRONTMATTER)
        fm.assert_called_once()

    def test_deny_has_no_frontmatter_blocks(self):
        """On deny, frontmatter is never run so no corrected blocks in reason."""
        with patch("pre_write_gate._run_health", return_value=VIOLATIONS):
            code, out = _call_main(_event("Write", "/src/Foo.swift", LONG_SWIFT))
        h = parse_hook_output(out)
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

    def test_edit_unreadable_file_sets_new_string_to_corrected(self):
        """When the file can't be read, content == new_string; corrected is the snippet-level
        fix, so new_string gets the corrected snippet — no full-file replacement needed."""
        with patch("pre_write_gate._run_frontmatter", return_value=CORRECTED_FRONTMATTER), \
             patch("pre_write_gate._run_health", return_value=[]):
            code, out = _call_main(_event("Edit", "/src/Foo.swift", LONG_SWIFT_WITH_FRONTMATTER))
        updated = parse_hook_output(out)["updatedInput"]
        self.assertIn("new_string", updated)
        self.assertEqual(updated["new_string"], CORRECTED_FRONTMATTER)

    def test_edit_existing_file_replaces_whole_file_to_prevent_duplication(self):
        """When the existing file is readable, _run_frontmatter receives the full post-edit
        content and returns a full corrected file.  _allow_corrected must set
        old_string=existing so the Edit replaces the whole file — not insert the
        full corrected content in place of the small old_string (which duplicates)."""
        existing_content = (
            "/**\n solid-name: Foo\n solid-category: service\n"
            " solid-description: Loads via URLSession.shared.\n */\n"
            "final class Foo {\n    func old() {}\n}\n"
        )
        corrected_content = (
            "/**\n solid-name: Foo\n solid-category: service\n"
            " solid-description: Coordinates data retrieval.\n */\n"
            "final class Foo {\n    func updated() {}\n}\n"
        )

        with tempfile.NamedTemporaryFile(suffix=".swift", mode="w", delete=False, encoding="utf-8") as f:
            f.write(existing_content)
            tmp_path = f.name

        try:
            event = {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": tmp_path,
                    "old_string": "    func old() {}\n",
                    "new_string": "    func updated() {}\n",
                },
                "session_id": "test",
            }
            with patch("pre_write_gate._run_frontmatter", return_value=corrected_content), \
                 patch("pre_write_gate._run_health", return_value=[]):
                code, out = _call_main(event)
        finally:
            os.unlink(tmp_path)

        updated = parse_hook_output(out)["updatedInput"]
        self.assertEqual(updated["old_string"], existing_content,
                         "old_string must be the full existing file to prevent duplication")
        self.assertEqual(updated["new_string"], corrected_content)
        self.assertNotIn("replace_all", updated)

    def test_no_frontmatter_health_clean_allows(self):
        """No solid-description means frontmatter correction is skipped.
        Health check still runs; if clean it allows silently."""
        with patch("pre_write_gate._run_frontmatter") as fm, \
             patch("pre_write_gate._run_health", return_value=[]) as hc:
            code, out = _call_main(_event("Write", "/src/Foo.swift", SHORT_SWIFT))
        hc.assert_called_once()
        fm.assert_not_called()
        self.assertEqual(out, "")

    def test_malformed_stdin_allows(self):
        code, out = test_utils.call_main_with_invalid_stdin(gate.main)
        self.assertEqual(code, 0)


PYTHON_CONTENT = (
    "class DataManager:\n"
    "    def read_file(self, path):\n"
    "        with open(path) as f:\n"
    "            return f.read()\n"
    "    def send_request(self, url):\n"
    "        import urllib.request\n"
    "        return urllib.request.urlopen(url).read()\n"
    "    def format_output(self, data):\n"
    "        return str(data).strip()\n"
)

_SRP_VIOLATION_WITH_METRIC = [
    {"principle": "SRP", "metric_id": "SRP-1", "issue": "Multiple responsibilities", "fix": "Extract concerns"}
]


class TestGatePythonSupport(unittest.TestCase):
    def test_py_file_invokes_run_health(self):
        with patch("pre_write_gate._run_frontmatter", return_value=PYTHON_CONTENT), \
             patch("pre_write_gate._run_health", return_value=[]) as hc:
            _call_main(_event("Write", "/src/Foo.py", PYTHON_CONTENT))
        hc.assert_called_once()

    def test_py_file_clean_allows(self):
        with patch("pre_write_gate._run_frontmatter", return_value=PYTHON_CONTENT), \
             patch("pre_write_gate._run_health", return_value=[]):
            code, out = _call_main(_event("Write", "/src/Foo.py", PYTHON_CONTENT))
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_py_file_violation_denies(self):
        with patch("pre_write_gate._run_frontmatter", return_value=PYTHON_CONTENT), \
             patch("pre_write_gate._run_health", return_value=VIOLATIONS):
            code, out = _call_main(_event("Write", "/src/Foo.py", PYTHON_CONTENT))
        h = parse_hook_output(out)
        self.assertEqual(h["permissionDecision"], "deny")
        self.assertIn("SRP", h["permissionDecisionReason"])

    def test_kt_file_skips_run_health(self):
        with patch("pre_write_gate._run_health") as hc:
            code, out = _call_main(_event("Write", "/src/Foo.kt", PYTHON_CONTENT))
        hc.assert_not_called()
        self.assertEqual(code, 0)

    def test_py_violation_with_metric_id_denies_with_issue_in_reason(self):
        with patch("pre_write_gate._run_frontmatter", return_value=PYTHON_CONTENT), \
             patch("pre_write_gate._run_health", return_value=_SRP_VIOLATION_WITH_METRIC):
            code, out = _call_main(_event("Write", "/src/Foo.py", PYTHON_CONTENT))
        h = parse_hook_output(out)
        self.assertEqual(h["permissionDecision"], "deny")
        self.assertIn("SRP", h["permissionDecisionReason"])
        self.assertIn("Multiple responsibilities", h["permissionDecisionReason"])


if __name__ == "__main__":
    unittest.main()
