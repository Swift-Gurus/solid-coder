"""
solid-name: test_run_started_event_recorder
solid-category: unit-test
solid-spec: [SPEC-031]
solid-description: Tests recording a run's start event via the shared event log.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.run_started_event_recorder import RunStartedEventRecorder


class SpyEventAppender:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def append(self, path: str, event_type: str, payload: dict) -> None:
        self.calls.append((path, event_type, payload))


class TestRunStartedEventRecorder(unittest.TestCase):

    def test_appends_a_run_started_event_with_the_run_id_and_flow_name(self):
        appender = SpyEventAppender()
        sut = RunStartedEventRecorder(event_appender=appender)

        sut.record("/runs/run-1/events.jsonl", "run-1", "code_review")

        self.assertEqual(appender.calls, [
            ("/runs/run-1/events.jsonl", "run_started", {"run_id": "run-1", "flow": "code_review"}),
        ])


if __name__ == "__main__":
    unittest.main()
