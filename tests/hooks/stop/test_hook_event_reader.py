"""
solid-name: test_hook_event_reader
solid-category: unit-test
solid-description: Validates hook event parsing with error logging and graceful handling of invalid input.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from on_stop import HookEventReader
from stop_handler_doubles import RecordingLogger, StubEventSource


class TestHookEventReader(unittest.TestCase):
    def test_reads_and_parses_json_from_source(self):
        reader = HookEventReader(source=StubEventSource('{"session_id": "abc"}'))

        self.assertEqual(reader.read(), {"session_id": "abc"})

    def test_empty_input_returns_empty_dict(self):
        reader = HookEventReader(source=StubEventSource("   "))

        self.assertEqual(reader.read(), {})

    def test_invalid_json_logs_and_returns_empty_dict(self):
        logger = RecordingLogger()
        reader = HookEventReader(source=StubEventSource("not json"), logger=logger)

        self.assertEqual(reader.read(), {})
        self.assertEqual(len(logger.messages), 1)


if __name__ == "__main__":
    unittest.main()
