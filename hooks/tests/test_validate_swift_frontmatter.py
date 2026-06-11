"""Tests for validate_swift_frontmatter.py"""

import json
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

HOOKS_DIR = str(Path(__file__).resolve().parents[1])
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

import validate_swift_frontmatter as hook
from test_utils import call_main, event

BAD_CONTENT = """\
/**
 solid-name: DataLoader
 solid-category: service
 solid-description: Loads data using URLSession.shared and calls MyStorageManager.
 */
final class DataLoader {
    func load() {}
}
"""

CLEAN_CONTENT = """\
/**
 solid-name: DataLoader
 solid-category: service
 solid-description: Fetches remote data asynchronously and persists results to local storage.
 */
final class DataLoader {
    func load() {}
}
"""

BAD_PY_CONTENT = '''
"""
solid-name: loader
solid-category: service
solid-description: Loads data using requests.Session() and calls StorageManager.save().
"""

def load():
    pass
'''

CLEAN_PY_CONTENT = '''
"""
solid-name: loader
solid-category: service
solid-description: Fetches remote data and persists results to local storage.
"""

def load():
    pass
'''


def _llm_raw(content: str) -> str:
    """Simulate the raw string returned by the LLM runner — a JSON object."""
    return json.dumps({"corrected_content": content})


def _mock_runner(return_value):
    """Return a mock runner whose .run() returns return_value."""
    runner = MagicMock()
    runner.run.return_value = return_value
    return runner


class TestParseCorrectedContent(unittest.TestCase):
    """Tests for the corrected_content extraction path via hook_utils.parse_json_field."""

    def _parse(self, raw):
        from hook_utils import parse_json_field, StrValidator
        v = parse_json_field(raw, "corrected_content", StrValidator())
        return v if v is not None else None

    def test_extracts_corrected_content_from_plain_json(self):
        raw = json.dumps({"corrected_content": CLEAN_CONTENT})
        self.assertEqual(self._parse(raw), CLEAN_CONTENT)

    def test_extracts_corrected_content_with_code_fence(self):
        raw = "\n" + json.dumps({"corrected_content": CLEAN_CONTENT}) + "\n"
        self.assertEqual(self._parse(raw), CLEAN_CONTENT)

    def test_extracts_corrected_content_with_surrounding_text(self):
        raw = "Here is the result:\n" + json.dumps({"corrected_content": CLEAN_CONTENT}) + "\nDone."
        self.assertEqual(self._parse(raw), CLEAN_CONTENT)

    def test_returns_none_for_missing_field(self):
        self.assertIsNone(self._parse(json.dumps({"other_field": "value"})))

    def test_returns_none_for_invalid_json(self):
        self.assertIsNone(self._parse("not json at all"))

    def test_returns_none_for_empty_string(self):
        self.assertIsNone(self._parse(""))

    def test_returns_none_when_corrected_content_is_not_string(self):
        self.assertIsNone(self._parse(json.dumps({"corrected_content": 42})))


class TestFix(unittest.TestCase):
    def test_returns_corrected_content_from_llm(self):
        with patch("validate_swift_frontmatter.make_llm_runner", return_value=_mock_runner(_llm_raw(CLEAN_CONTENT))):
            result = hook.fix(BAD_CONTENT)
        self.assertEqual(result, CLEAN_CONTENT)

    def test_returns_unchanged_content_when_llm_echoes_back(self):
        with patch("validate_swift_frontmatter.make_llm_runner", return_value=_mock_runner(_llm_raw(CLEAN_CONTENT))):
            result = hook.fix(CLEAN_CONTENT)
        self.assertEqual(result, CLEAN_CONTENT)

    def test_raises_when_runner_raises(self):
        from hook_utils import SubprocessError
        runner = MagicMock()
        runner.run.side_effect = SubprocessError("subprocess died")
        with patch("validate_swift_frontmatter.make_llm_runner", return_value=runner):
            with self.assertRaises(SubprocessError):
                hook.fix(BAD_CONTENT)

    def test_returns_none_when_llm_returns_plain_text_instead_of_json(self):
        with patch("validate_swift_frontmatter.make_llm_runner", return_value=_mock_runner(CLEAN_CONTENT)):
            self.assertIsNone(hook.fix(BAD_CONTENT))

    def test_includes_parent_session_header_in_prompt(self):
        captured_prompts = []
        runner = MagicMock()
        runner.run.side_effect = lambda prompt, **kw: (captured_prompts.append(prompt), _llm_raw(CLEAN_CONTENT))[1]
        with patch("validate_swift_frontmatter.make_llm_runner", return_value=runner):
            hook.fix(BAD_CONTENT, parent_session_id="sess-123")
        self.assertIn("spawned-by: sess-123", captured_prompts[0])

    def test_runner_called_with_bare_session_timeout(self):
        runner = MagicMock()
        runner.run.return_value = _llm_raw(CLEAN_CONTENT)
        with patch("validate_swift_frontmatter.make_llm_runner", return_value=runner), \
             patch("validate_swift_frontmatter.bare_session_timeout", return_value=42):
            hook.fix(BAD_CONTENT)
        _, kwargs = runner.run.call_args
        self.assertEqual(kwargs.get("timeout"), 42)

    def test_runner_created_with_no_mcp_config(self):
        runner = MagicMock()
        runner.run.return_value = _llm_raw(CLEAN_CONTENT)
        with patch("validate_swift_frontmatter.make_llm_runner", return_value=runner) as mock_factory:
            hook.fix(BAD_CONTENT)
        _, kwargs = mock_factory.call_args
        self.assertEqual(kwargs.get("mcp_config"), "")


class TestMainHook(unittest.TestCase):
    def _patch_runner(self, return_value=None):
        return patch("validate_swift_frontmatter.make_llm_runner",
                     return_value=_mock_runner(return_value))

    def test_unsupported_file_type_allows_without_llm(self):
        with self._patch_runner() as mock_factory:
            code, out = call_main(event("Write", "/src/Foo.js", BAD_CONTENT), hook.main)
        mock_factory.assert_not_called()
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_py_file_with_solid_description_is_processed(self):
        with self._patch_runner(_llm_raw(CLEAN_PY_CONTENT)):
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
        with self._patch_runner(_llm_raw(CLEAN_CONTENT)):
            code, out = call_main(event("Write", "/src/Foo.swift", BAD_CONTENT), hook.main)
        self.assertEqual(code, 0)
        payload = json.loads(out)
        updated = payload["hookSpecificOutput"]["updatedInput"]
        self.assertEqual(updated["content"], CLEAN_CONTENT)
        self.assertEqual(updated["file_path"], "/src/Foo.swift")

    def test_already_clean_content_allows_without_updatedInput(self):
        with self._patch_runner(_llm_raw(CLEAN_CONTENT)):
            code, out = call_main(event("Write", "/src/Foo.swift", CLEAN_CONTENT), hook.main)
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_edit_tool_uses_new_string_key(self):
        with self._patch_runner(_llm_raw(CLEAN_CONTENT)):
            code, out = call_main(event("Edit", "/src/Foo.swift", BAD_CONTENT), hook.main)
        payload = json.loads(out)
        self.assertEqual(payload["hookSpecificOutput"]["updatedInput"]["new_string"], CLEAN_CONTENT)

    def test_edit_preserves_old_string_in_updated_input(self):
        with self._patch_runner(_llm_raw(CLEAN_CONTENT)):
            code, out = call_main(event("Edit", "/src/Foo.swift", BAD_CONTENT), hook.main)
        payload = json.loads(out)
        self.assertEqual(payload["hookSpecificOutput"]["updatedInput"]["old_string"], "old")

    def test_llm_failure_causes_nonblocking_exit(self):
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
        with self._patch_runner(_llm_raw(CLEAN_CONTENT)):
            code, out = call_main(event("Write", "/src/Foo.swift", BAD_CONTENT), hook.main)
        payload = json.loads(out)
        self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "allow")


if __name__ == "__main__":
    unittest.main()