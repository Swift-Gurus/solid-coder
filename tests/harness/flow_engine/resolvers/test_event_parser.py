"""
solid-name: test_event_parser
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests parsing raw event log lines into structured events, skipping corrupt lines.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.event_replayer import EventParser


class TestEventParser(unittest.TestCase):

    def setUp(self):
        self.sut = EventParser()

    def test_parses_valid_json_lines(self):
        events = self.sut.parse(['{"event": "run_completed"}', '{"event": "run_timed_out"}'])
        self.assertEqual(events, [{"event": "run_completed"}, {"event": "run_timed_out"}])

    def test_skips_corrupt_lines(self):
        events = self.sut.parse(['{"event": "run_completed"}', "not valid json {{{"])
        self.assertEqual(events, [{"event": "run_completed"}])

    def test_skips_blank_lines(self):
        events = self.sut.parse(["", "  ", '{"event": "run_completed"}'])
        self.assertEqual(events, [{"event": "run_completed"}])


if __name__ == "__main__":
    unittest.main()
