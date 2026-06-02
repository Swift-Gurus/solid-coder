"""Tests for validate_swift_frontmatter.py"""

import json
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

HOOKS_DIR = str(Path(__file__).resolve().parents[1])
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

import validate_swift_frontmatter as hook

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

BAD_PY_CONTENT = '''\
"""
solid-name: loader
solid-category: service
solid-description: Loads data using requests.Session() and calls StorageManager.save().
"""

def load():
    pass
'''

CLEAN_PY_CONTENT = '''\
"""
solid-name: loader
solid-category: service
solid-description: Fetches remote data and persists results to local storage.
"""

def load():
    pass
'''


def _llm_raw(content: str) -> str:
    """Simulate the raw string returned by run_claude_bare — a JSON object."""
    return json.dumps({"corrected_content": content})


def _call_main(stdin_json: dict) -> tuple:
    stdout_buf = io.StringIO()
    exit_code = 0
    with patch("sys.stdin", io.StringIO(json.dumps(stdin_json))):
        with redirect_stdout(stdout_buf):
            try:
                hook.main()
            except SystemExit as e:
                exit_code = e.code or 0
    return exit_code, stdout_buf.getvalue()


def _write_event(file_path: str, content: str) -> dict:
    return {
        "tool_name": "Write",
        "tool_input": {"file_path": file_path, "content": content},
        "session_id": "test-session",
    }


def _edit_event(file_path: str, new_string: str) -> dict:
    return {
        "tool_name": "Edit",
        "tool_input": {"file_path": file_path, "old_string": "old", "new_string": new_string},
        "session_id": "test-session",
    }


class TestParseCorreected(unittest.TestCase):
    def test_extracts_corrected_content_from_plain_json(self):
        raw = json.dumps({"corrected_content": CLEAN_CONTENT})
        self.assertEqual(hook._parse_corrected(raw), CLEAN_CONTENT)

    def test_extracts_corrected_content_with_code_fence(self):
        raw = "```json\n" + json.dumps({"corrected_content": CLEAN_CONTENT}) + "\n```"
        self.assertEqual(hook._parse_corrected(raw), CLEAN_CONTENT)

    def test_extracts_corrected_content_with_surrounding_text(self):
        raw = "Here is the result:\n" + json.dumps({"corrected_content": CLEAN_CONTENT}) + "\nDone."
        self.assertEqual(hook._parse_corrected(raw), CLEAN_CONTENT)

    def test_returns_none_for_missing_field(self):
        raw = json.dumps({"other_field": "value"})
        self.assertIsNone(hook._parse_corrected(raw))

    def test_returns_none_for_invalid_json(self):
        self.assertIsNone(hook._parse_corrected("not json at all"))

    def test_returns_none_for_empty_string(self):
        self.assertIsNone(hook._parse_corrected(""))

    def test_returns_none_when_corrected_content_is_not_string(self):
        raw = json.dumps({"corrected_content": 42})
        self.assertIsNone(hook._parse_corrected(raw))


class TestFix(unittest.TestCase):
    def test_returns_corrected_content_from_llm(self):
        with patch("validate_swift_frontmatter.run_claude_bare", return_value=_llm_raw(CLEAN_CONTENT)):
            result = hook.fix(BAD_CONTENT)
        self.assertEqual(result, CLEAN_CONTENT)

    def test_returns_unchanged_content_when_llm_echoes_back(self):
        with patch("validate_swift_frontmatter.run_claude_bare", return_value=_llm_raw(CLEAN_CONTENT)):
            result = hook.fix(CLEAN_CONTENT)
        self.assertEqual(result, CLEAN_CONTENT)

    def test_returns_none_when_run_claude_bare_returns_none(self):
        with patch("validate_swift_frontmatter.run_claude_bare", return_value=None):
            self.assertIsNone(hook.fix(BAD_CONTENT))

    def test_returns_none_when_llm_returns_plain_text_instead_of_json(self):
        with patch("validate_swift_frontmatter.run_claude_bare", return_value=CLEAN_CONTENT):
            self.assertIsNone(hook.fix(BAD_CONTENT))

    def test_includes_parent_session_header_in_prompt(self):
        captured_prompts = []

        def capture(prompt, **kwargs):
            captured_prompts.append(prompt)
            return _llm_raw(CLEAN_CONTENT)

        with patch("validate_swift_frontmatter.run_claude_bare", side_effect=capture):
            hook.fix(BAD_CONTENT, parent_session_id="sess-123")

        self.assertIn("spawned-by: sess-123", captured_prompts[0])


class TestMainHook(unittest.TestCase):
    def test_unsupported_file_type_allows_without_llm(self):
        with patch("validate_swift_frontmatter.run_claude_bare") as mock_run:
            code, out = _call_main(_write_event("/src/Foo.js", BAD_CONTENT))
        mock_run.assert_not_called()
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_py_file_with_solid_description_is_processed(self):
        with patch("validate_swift_frontmatter.run_claude_bare", return_value=_llm_raw(CLEAN_PY_CONTENT)):
            code, out = _call_main(_write_event("/src/loader.py", BAD_PY_CONTENT))
        self.assertEqual(code, 0)
        payload = json.loads(out)
        updated = payload["hookSpecificOutput"]["updatedInput"]
        self.assertEqual(updated["content"], CLEAN_PY_CONTENT)

    def test_no_solid_description_allows_without_llm(self):
        with patch("validate_swift_frontmatter.run_claude_bare") as mock_run:
            code, out = _call_main(_write_event("/src/Foo.swift", "final class Foo {}\n"))
        mock_run.assert_not_called()
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_unknown_tool_allows_without_llm(self):
        event = {"tool_name": "Read", "tool_input": {"file_path": "/src/Foo.swift"}, "session_id": "s"}
        with patch("validate_swift_frontmatter.run_claude_bare") as mock_run:
            code, _ = _call_main(event)
        mock_run.assert_not_called()
        self.assertEqual(code, 0)

    def test_bad_frontmatter_write_returns_allow_with_corrected_content(self):
        with patch("validate_swift_frontmatter.run_claude_bare", return_value=_llm_raw(CLEAN_CONTENT)):
            code, out = _call_main(_write_event("/src/Foo.swift", BAD_CONTENT))
        self.assertEqual(code, 0)
        payload = json.loads(out)
        updated = payload["hookSpecificOutput"]["updatedInput"]
        self.assertEqual(updated["content"], CLEAN_CONTENT)
        self.assertEqual(updated["file_path"], "/src/Foo.swift")

    def test_already_clean_content_allows_without_updatedInput(self):
        with patch("validate_swift_frontmatter.run_claude_bare", return_value=_llm_raw(CLEAN_CONTENT)):
            code, out = _call_main(_write_event("/src/Foo.swift", CLEAN_CONTENT))
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_edit_tool_uses_new_string_key(self):
        with patch("validate_swift_frontmatter.run_claude_bare", return_value=_llm_raw(CLEAN_CONTENT)):
            code, out = _call_main(_edit_event("/src/Foo.swift", BAD_CONTENT))
        payload = json.loads(out)
        updated = payload["hookSpecificOutput"]["updatedInput"]
        self.assertEqual(updated["new_string"], CLEAN_CONTENT)

    def test_edit_preserves_old_string_in_updated_input(self):
        with patch("validate_swift_frontmatter.run_claude_bare", return_value=_llm_raw(CLEAN_CONTENT)):
            code, out = _call_main(_edit_event("/src/Foo.swift", BAD_CONTENT))
        payload = json.loads(out)
        self.assertEqual(payload["hookSpecificOutput"]["updatedInput"]["old_string"], "old")

    def test_llm_failure_fails_open(self):
        with patch("validate_swift_frontmatter.run_claude_bare", return_value=None):
            code, out = _call_main(_write_event("/src/Foo.swift", BAD_CONTENT))
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_llm_ignores_schema_fails_open(self):
        with patch("validate_swift_frontmatter.run_claude_bare", return_value=CLEAN_CONTENT):
            code, out = _call_main(_write_event("/src/Foo.swift", BAD_CONTENT))
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_malformed_stdin_allows(self):
        with patch("sys.stdin", io.StringIO("not json")):
            try:
                hook.main()
            except SystemExit as e:
                self.assertEqual(e.code or 0, 0)

    def test_permission_decision_is_allow(self):
        with patch("validate_swift_frontmatter.run_claude_bare", return_value=_llm_raw(CLEAN_CONTENT)):
            code, out = _call_main(_write_event("/src/Foo.swift", BAD_CONTENT))
        payload = json.loads(out)
        self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "allow")


if __name__ == "__main__":
    unittest.main()
