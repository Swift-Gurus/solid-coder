"""Tests for pre_write_gate.py — allow/deny decisions once health and frontmatter checks run."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

import test_utils
from _gate_fixtures import (
    CORRECTED_FRONTMATTER,
    FM,
    HC,
    LONG_SWIFT,
    LONG_SWIFT_WITH_FRONTMATTER,
    SHORT_SWIFT,
    VIOLATIONS,
    call_main,
    event,
)
from test_utils import parse_hook_output


class TestGateDecisions(unittest.TestCase):
    def test_both_clean_allows(self):
        with patch(FM, return_value=LONG_SWIFT_WITH_FRONTMATTER), patch(HC, return_value=[]):
            code, out = call_main(event("Write", "/src/Foo.swift", LONG_SWIFT_WITH_FRONTMATTER))
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_health_violations_blocks_without_running_frontmatter(self):
        """Health violations deny the write — frontmatter fix is never reached."""
        with patch(FM) as fm, patch(HC, return_value=VIOLATIONS):
            code, out = call_main(event("Write", "/src/Foo.swift", LONG_SWIFT_WITH_FRONTMATTER))
        h = parse_hook_output(out)
        self.assertEqual(h["permissionDecision"], "deny")
        self.assertIn("SRP", h["permissionDecisionReason"])
        self.assertIn("The file was NOT written", h["permissionDecisionReason"])
        fm.assert_not_called()

    def test_frontmatter_correction_only_runs_when_health_passes(self):
        """Frontmatter runs after health check returns clean."""
        with patch(FM, return_value=CORRECTED_FRONTMATTER) as fm, patch(HC, return_value=[]):
            code, out = call_main(event("Write", "/src/Foo.swift", LONG_SWIFT_WITH_FRONTMATTER))
        h = parse_hook_output(out)
        self.assertEqual(h["permissionDecision"], "allow")
        self.assertEqual(h["updatedInput"]["content"], CORRECTED_FRONTMATTER)
        fm.assert_called_once()

    def test_deny_has_no_frontmatter_blocks(self):
        """On deny, frontmatter is never run so no corrected blocks in reason."""
        with patch(HC, return_value=VIOLATIONS):
            code, out = call_main(event("Write", "/src/Foo.swift", LONG_SWIFT))
        h = parse_hook_output(out)
        self.assertEqual(h["permissionDecision"], "deny")
        self.assertNotIn("corrected frontmatter", h["permissionDecisionReason"])

    def test_frontmatter_error_fails_open(self):
        with patch(FM, return_value=None), patch(HC, return_value=[]):
            code, out = call_main(event("Write", "/src/Foo.swift", LONG_SWIFT_WITH_FRONTMATTER))
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_health_error_fails_open(self):
        with patch(FM, return_value=LONG_SWIFT), patch(HC, return_value=None):
            code, out = call_main(event("Write", "/src/Foo.swift", LONG_SWIFT))
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_edit_unreadable_file_sets_new_string_to_corrected(self):
        """When the file can't be read, new_string gets the corrected snippet."""
        with patch(FM, return_value=CORRECTED_FRONTMATTER), patch(HC, return_value=[]):
            code, out = call_main(event("Edit", "/src/Foo.swift", LONG_SWIFT_WITH_FRONTMATTER))
        updated = parse_hook_output(out)["updatedInput"]
        self.assertIn("new_string", updated)
        self.assertEqual(updated["new_string"], CORRECTED_FRONTMATTER)

    def test_edit_existing_file_replaces_whole_file_to_prevent_duplication(self):
        """When the existing file is readable, old_string is set to the full existing content."""
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
            ev = {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": tmp_path,
                    "old_string": "    func old() {}\n",
                    "new_string": "    func updated() {}\n",
                },
                "session_id": "test",
            }
            with patch(FM, return_value=corrected_content), patch(HC, return_value=[]):
                code, out = call_main(ev)
        finally:
            os.unlink(tmp_path)

        updated = parse_hook_output(out)["updatedInput"]
        self.assertEqual(updated["old_string"], existing_content)
        self.assertEqual(updated["new_string"], corrected_content)
        self.assertNotIn("replace_all", updated)

    def test_no_frontmatter_health_clean_allows(self):
        """No solid-description means frontmatter correction is skipped."""
        with patch(FM) as fm, patch(HC, return_value=[]) as hc:
            code, out = call_main(event("Write", "/src/Foo.swift", SHORT_SWIFT))
        hc.assert_called_once()
        fm.assert_not_called()
        self.assertEqual(out, "")

    def test_malformed_stdin_allows(self):
        import pre_write_gate as gate
        code, out = test_utils.call_main_with_invalid_stdin(gate.main)
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
