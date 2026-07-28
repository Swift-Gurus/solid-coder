"""
solid-description: Validates parsing of Stop/SubagentStop hook payloads into a typed StopHookEvent.
solid-category: unit-test
"""

import json
import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

from hook_utils import StopHookEvent, parse_stop_hook_event  # noqa: E402


class TestParseStopHookEvent(unittest.TestCase):
    def test_parses_all_known_fields(self):
        raw = json.dumps({
            "stop_hook_active": True,
            "session_id": "sess-1",
            "transcript_path": "/tmp/transcript.jsonl",
            "cwd": "/Users/alex/Developer/build-mobile",
            "last_assistant_message": "done",
        })

        event = parse_stop_hook_event(raw)

        self.assertEqual(event, StopHookEvent(
            stop_hook_active=True, session_id="sess-1", transcript_path="/tmp/transcript.jsonl",
            cwd="/Users/alex/Developer/build-mobile", last_assistant_message="done",
        ))

    def test_missing_fields_default_to_falsy_values(self):
        event = parse_stop_hook_event(json.dumps({}))

        self.assertEqual(event, StopHookEvent())
        self.assertFalse(event.stop_hook_active)

    def test_returns_none_for_invalid_json(self):
        self.assertIsNone(parse_stop_hook_event("not json"))


if __name__ == "__main__":
    unittest.main()
