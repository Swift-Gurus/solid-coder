"""
solid-name: TestEventAppender
solid-description: Verifies that events are correctly appended and persisted.
solid-category: unit-test
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.event_appender import EventAppender, EventSerializer, POSIXFileAppender


class TestEventAppender(unittest.TestCase):

    def setUp(self):
        self.appender = EventAppender(serializer=EventSerializer(), file_appender=POSIXFileAppender())
        self._temp_files: list[str] = []

    def tearDown(self):
        for path in self._temp_files:
            try:
                os.unlink(path)
            except OSError:
                pass

    def _create_temp_jsonl(self) -> str:
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        self._temp_files.append(path)
        return path

    def test_appends_typed_event_to_file(self):
        path = self._create_temp_jsonl()
        self.appender.append(path, "step_started", {"step_id": "my_step"})
        lines = Path(path).read_text().strip().splitlines()
        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])
        self.assertEqual(record["event"], "step_started")
        self.assertEqual(record["step_id"], "my_step")
        self.assertIn("ts", record)

    def test_multiple_appends_produce_multiple_lines(self):
        path = self._create_temp_jsonl()
        for i in range(3):
            self.appender.append(path, "turn_counted", {"total": i + 1})
        lines = Path(path).read_text().strip().splitlines()
        self.assertEqual(len(lines), 3)

    def test_each_line_is_valid_json(self):
        path = self._create_temp_jsonl()
        self.appender.append(path, "run_completed", {})
        self.appender.append(path, "step_started", {"step_id": "a"})
        for line in Path(path).read_text().strip().splitlines():
            parsed = json.loads(line)
            self.assertIn("event", parsed)


if __name__ == "__main__":
    unittest.main()
