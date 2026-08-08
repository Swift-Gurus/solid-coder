"""
solid-name: TestEventReplayer
solid-description: Validates that replay delegates parsing and reconstruction to its injected collaborators.
solid-category: unit-test
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.event_replayer import EventParser, EventReplayer
from harness.models import RunState
from harness.run_state_reconstructor_factory import make_run_state_reconstructor


class StubParser:
    def __init__(self, events: list[dict]) -> None:
        self._events = events

    def parse(self, lines: list[str]) -> list[dict]:
        return self._events


class SpyReconstructor:
    def __init__(self, run_state: RunState) -> None:
        self._run_state = run_state
        self.calls: list[list[dict]] = []

    def reconstruct(self, events: list[dict]) -> RunState:
        self.calls.append(events)
        return self._run_state


class TestEventReplayer(unittest.TestCase):

    def test_missing_file_returns_not_started_without_reading(self):
        reconstructor = SpyReconstructor(RunState(completed={}, running=[], turn_count=0, status="in_progress"))
        replayer = EventReplayer(parser=StubParser([]), reconstructor=reconstructor)

        state = replayer.replay("/nonexistent/path/events.jsonl")

        self.assertEqual(state.status, "not_started")
        self.assertEqual(state.turn_count, 0)
        self.assertEqual(reconstructor.calls, [])

    def test_delegates_parsed_events_to_reconstructor(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w", delete=False) as f:
            f.write(json.dumps({"event": "run_completed"}) + "\n")
            path = f.name

        expected_state = RunState(completed={}, running=[], turn_count=3, status="done")
        events = [{"event": "run_completed"}]
        reconstructor = SpyReconstructor(expected_state)
        replayer = EventReplayer(parser=StubParser(events), reconstructor=reconstructor)

        state = replayer.replay(path)

        self.assertIs(state, expected_state)
        self.assertEqual(reconstructor.calls, [events])

    def test_replays_a_real_event_log_end_to_end(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w", delete=False) as f:
            f.write(json.dumps({"event": "step_completed", "step_id": "a", "outputs": {}}) + "\n")
            f.write(json.dumps({"event": "run_completed"}) + "\n")
            path = f.name

        replayer = EventReplayer(parser=EventParser(), reconstructor=make_run_state_reconstructor())

        state = replayer.replay(path)

        self.assertIn("a", state.completed)
        self.assertEqual(state.status, "done")


if __name__ == "__main__":
    unittest.main()
