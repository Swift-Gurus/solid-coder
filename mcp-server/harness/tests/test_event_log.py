"""
solid-name: TestEventReplayer
solid-description: Validates correct run state reconstruction from event logs.
solid-category: unit-test
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from harness.event_replayer import EventParser, EventReplayer
from harness.models import StepOutputs


class TestEventReplayer(unittest.TestCase):

    def setUp(self):
        self.replayer = EventReplayer(parser=EventParser())

    def _write_events(self, path: Path, events: list[dict]) -> None:
        with open(path, "w") as f:
            for e in events:
                f.write(json.dumps(e) + "\n")

    def test_missing_file_returns_not_started(self):
        state = self.replayer.replay("/nonexistent/path/events.jsonl")
        self.assertEqual(state.status, "not_started")
        self.assertEqual(state.turn_count, 0)

    def test_step_started_and_completed(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = f.name
        self._write_events(Path(path), [
            {"event": "step_started", "step_id": "load_principles"},
            {"event": "step_completed", "step_id": "load_principles", "outputs": {"principles": ["SRP"]}},
        ])
        state = self.replayer.replay(path)
        self.assertIn("load_principles", state.completed)
        self.assertNotIn("load_principles", state.running)
        self.assertIsInstance(state.completed["load_principles"], StepOutputs)
        self.assertEqual(state.completed["load_principles"].get("principles"), ["SRP"])

    def test_turn_count_accumulates(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = f.name
        self._write_events(Path(path), [
            {"event": "turn_counted", "total": 1},
            {"event": "turn_counted", "total": 2},
        ])
        state = self.replayer.replay(path)
        self.assertEqual(state.turn_count, 2)

    def test_run_completed_sets_done(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = f.name
        self._write_events(Path(path), [{"event": "run_completed"}])
        state = self.replayer.replay(path)
        self.assertEqual(state.status, "done")

    def test_run_timed_out_sets_timed_out(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = f.name
        self._write_events(Path(path), [{"event": "run_timed_out"}])
        state = self.replayer.replay(path)
        self.assertEqual(state.status, "timed_out")

    def test_corrupt_line_skipped(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w", delete=False) as f:
            f.write('{"event": "run_completed"}\n')
            f.write("not valid json {{{\n")
            path = f.name
        state = self.replayer.replay(path)
        self.assertEqual(state.status, "done")


if __name__ == "__main__":
    unittest.main()
