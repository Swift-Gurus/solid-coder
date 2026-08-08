"""Tests for validate_swift_frontmatter.py — main() hook entry point behavior."""

import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

HOOKS_DIR = str(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks")
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

import validate_swift_frontmatter as hook
from _frontmatter_fixtures import BAD_CONTENT, BAD_PY_CONTENT, CLEAN_CONTENT, CLEAN_PY_CONTENT, llm_raw, mock_runner
from test_utils import call_main, event


class TestMainHook(unittest.TestCase):
    def _patch_runner(self, return_value=None):
        return patch("validate_swift_frontmatter.make_llm_runner",
                     return_value=mock_runner(return_value))

    def test_unsupported_file_type_allows_without_llm(self):
        with self._patch_runner() as mock_factory:
            code, out = call_main(event("Write", "/src/Foo.js", BAD_CONTENT), hook.main)
        mock_factory.assert_not_called()
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_py_file_with_solid_description_is_processed(self):
        with self._patch_runner(llm_raw(CLEAN_PY_CONTENT)):
            code, out = call_main(event("Write", "/src/loader.py", BAD_PY_CONTENT), hook.main)
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["hookSpecificOutput"]["updatedInput"]["content"], CLEAN_PY_CONTENT)

    def test_no_solid_description_allows_without_llm(self):
        with self._patch_runner() as mock_factory:
            code, out = call_main(event("Write", "/src/Foo.swift", "final class Foo {}\n"), hook.main)
        mock_factory.assert_not_called()
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_unknown_tool_allows_without_llm(self):
        read_event = {"tool_name": "Read", "tool_input": {"file_path": "/src/Foo.swift"}, "session_id": "s"}
        with self._patch_runner() as mock_factory:
            code, _ = call_main(read_event, hook.main)
        mock_factory.assert_not_called()
        self.assertEqual(code, 0)

    def test_bad_frontmatter_write_returns_allow_with_corrected_content(self):
        with self._patch_runner(llm_raw(CLEAN_CONTENT)):
            code, out = call_main(event("Write", "/src/Foo.swift", BAD_CONTENT), hook.main)
        self.assertEqual(code, 0)
        payload = json.loads(out)
        updated = payload["hookSpecificOutput"]["updatedInput"]
        self.assertEqual(updated["content"], CLEAN_CONTENT)
        self.assertEqual(updated["file_path"], "/src/Foo.swift")

    def test_already_clean_content_allows_without_updatedInput(self):
        with self._patch_runner(llm_raw(CLEAN_CONTENT)):
            code, out = call_main(event("Write", "/src/Foo.swift", CLEAN_CONTENT), hook.main)
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_edit_tool_uses_new_string_key(self):
        with self._patch_runner(llm_raw(CLEAN_CONTENT)):
            code, out = call_main(event("Edit", "/src/Foo.swift", BAD_CONTENT), hook.main)
        payload = json.loads(out)
        self.assertEqual(payload["hookSpecificOutput"]["updatedInput"]["new_string"], CLEAN_CONTENT)

    def test_edit_preserves_old_string_in_updated_input(self):
        with self._patch_runner(llm_raw(CLEAN_CONTENT)):
            code, out = call_main(event("Edit", "/src/Foo.swift", BAD_CONTENT), hook.main)
        payload = json.loads(out)
        self.assertEqual(payload["hookSpecificOutput"]["updatedInput"]["old_string"], "old")

    def test_llm_failure_causes_nonblocking_exit(self):
        from unittest.mock import MagicMock
        from hook_utils import SubprocessError
        runner = MagicMock()
        runner.run.side_effect = SubprocessError("subprocess died")
        with patch("validate_swift_frontmatter.make_llm_runner", return_value=runner):
            code, out = call_main(event("Write", "/src/Foo.swift", BAD_CONTENT), hook.main)
        self.assertNotEqual(code, 2)  # not a block — Claude Code treats as non-blocking allow
        self.assertEqual(out, "")

    def test_llm_ignores_schema_fails_open(self):
        with self._patch_runner(CLEAN_CONTENT):
            code, out = call_main(event("Write", "/src/Foo.swift", BAD_CONTENT), hook.main)
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_malformed_stdin_allows(self):
        with patch("sys.stdin", io.StringIO("not json")):
            try:
                hook.main()
            except SystemExit as e:
                self.assertEqual(e.code or 0, 0)

    def test_permission_decision_is_allow(self):
        with self._patch_runner(llm_raw(CLEAN_CONTENT)):
            code, out = call_main(event("Write", "/src/Foo.swift", BAD_CONTENT), hook.main)
        payload = json.loads(out)
        self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "allow")


if __name__ == "__main__":
    unittest.main()
