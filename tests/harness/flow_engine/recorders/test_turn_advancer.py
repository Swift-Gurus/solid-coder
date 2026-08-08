"""
solid-name: test_turn_advancer
solid-category: unit-test
solid-spec: [SPEC-031]
solid-description: Tests recording a completed turn and returning the run's replayed state afterward.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.models import RunState
from harness.turn_advancer import TurnAdvancer


class StubEventReplayer:
    def __init__(self, states: list[RunState]) -> None:
        self._states = list(states)
        self.calls: list[str] = []

    def replay(self, path: str) -> RunState:
        self.calls.append(path)
        return self._states[len(self.calls) - 1]


class SpyEventAppender:
    def __init__(self) -> None:
        self.events: list[tuple] = []

    def append(self, path: str, event_type: str, payload: dict) -> None:
        self.events.append((path, event_type, payload))


class TestTurnAdvancer(unittest.TestCase):

    def test_appends_turn_counted_with_incremented_total_and_returns_new_state(self):
        before = RunState(completed={}, running=[], turn_count=2, status="in_progress")
        after = RunState(completed={}, running=[], turn_count=3, status="in_progress")
        replayer = StubEventReplayer([before, after])
        appender = SpyEventAppender()
        sut = TurnAdvancer(event_replayer=replayer, event_appender=appender)

        result = sut.advance("/run/events.jsonl")

        self.assertIs(result, after)
        self.assertEqual(appender.events, [("/run/events.jsonl", "turn_counted", {"total": 3})])
        self.assertEqual(replayer.calls, ["/run/events.jsonl", "/run/events.jsonl"])


if __name__ == "__main__":
    unittest.main()
