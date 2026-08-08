"""
solid-name: test_output_recorder
solid-category: unit-test
solid-spec: [SPEC-031]
solid-description: Tests appending step_completed and session_step_recorded events for each ready step instance.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.models import StepInstance
from harness.output_recorder import OutputRecorder


class SpyEventAppender:
    def __init__(self) -> None:
        self.events: list[tuple] = []

    def append(self, path: str, event_type: str, payload: dict) -> None:
        self.events.append((path, event_type, payload))


class TestOutputRecorder(unittest.TestCase):

    def test_records_completion_and_session_mapping_per_instance(self):
        appender = SpyEventAppender()
        sut = OutputRecorder(event_appender=appender)
        instances = [
            StepInstance(step_id="step-a", instance_id="step-a-1", item=None, prompt="Do step-a"),
            StepInstance(step_id="step-b", instance_id="step-b-1", item=None, prompt="Do step-b"),
        ]

        sut.record("/run/events.jsonl", instances, {"step-a-1": {"result": "ok"}}, "session-42")

        event_types = [e[1] for e in appender.events]
        self.assertEqual(event_types, [
            "step_completed", "session_step_recorded",
            "step_completed", "session_step_recorded",
        ])
        first_completed = appender.events[0][2]
        self.assertEqual(first_completed["instance_id"], "step-a-1")
        self.assertEqual(first_completed["outputs"], {"result": "ok"})
        self.assertEqual(first_completed["session_id"], "session-42")

        second_completed = appender.events[2][2]
        self.assertEqual(second_completed["instance_id"], "step-b-1")
        self.assertEqual(second_completed["outputs"], {})

    def test_no_instances_records_nothing(self):
        appender = SpyEventAppender()
        sut = OutputRecorder(event_appender=appender)

        sut.record("/run/events.jsonl", [], {}, "session-1")

        self.assertEqual(appender.events, [])


if __name__ == "__main__":
    unittest.main()
