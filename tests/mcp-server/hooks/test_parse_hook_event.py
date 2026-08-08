"""
solid-description: Validates correct extraction of session working directory from event data with appropriate fallback.
solid-category: unit-test
"""

import json
import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks", Path(__file__).resolve().parent)

from hook_utils import parse_hook_event  # noqa: E402


class TestParseHookEventCwd(unittest.TestCase):
    def test_cwd_extracted_when_present(self):
        raw = json.dumps({
            "tool_name": "Write",
            "tool_input": {"file_path": "/repo/ios/Foo.swift"},
            "session_id": "sess-1",
            "cwd": "/Users/alex/Developer/build-mobile",
        })
        _, _, _, _, cwd = parse_hook_event(raw)
        self.assertEqual(cwd, "/Users/alex/Developer/build-mobile")

    def test_cwd_defaults_to_empty_string_when_absent(self):
        raw = json.dumps({
            "tool_name": "Write",
            "tool_input": {"file_path": "/repo/Foo.swift"},
            "session_id": "sess-1",
        })
        _, _, _, _, cwd = parse_hook_event(raw)
        self.assertEqual(cwd, "")

    def test_returns_five_tuple(self):
        raw = json.dumps({
            "tool_name": "Write",
            "tool_input": {"file_path": "/repo/Foo.swift"},
            "session_id": "sess-1",
            "cwd": "/repo",
        })
        parsed = parse_hook_event(raw)
        self.assertEqual(len(parsed), 5)

    def test_returns_none_for_invalid_json(self):
        self.assertIsNone(parse_hook_event("not json"))


if __name__ == "__main__":
    unittest.main()
