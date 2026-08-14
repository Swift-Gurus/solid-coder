"""
solid-name: test_output_recorder
solid-category: unit-test
solid-spec: [SPEC-031]
solid-description: Tests recording addressed step instances with iteration evidence and parent-completion state.
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

    def test_records_completion_and_session_mapping_per_addressed_instance(self):
        appender = SpyEventAppender()
        sut = OutputRecorder(event_appender=appender)
        instances = [
            StepInstance(step_id="step-a", instance_id="step-a-1", item=None, prompt="Do step-a"),
            StepInstance(step_id="step-b", instance_id="step-b-1", item=None, prompt="Do step-b"),
        ]

        sut.record(
            "/run/events.jsonl",
            instances,
            {
                "step-a-1": {"result": "a"},
                "step-b-1": {"result": "b"},
            },
            "session-42",
        )

        event_types = [e[1] for e in appender.events]
        self.assertEqual(event_types, [
            "step_completed", "session_step_recorded",
            "step_completed", "session_step_recorded",
        ])
        first_completed = appender.events[0][2]
        self.assertEqual(first_completed["instance_id"], "step-a-1")
        self.assertEqual(first_completed["outputs"], {"result": "a"})
        self.assertEqual(first_completed["session_id"], "session-42")
        self.assertIsNone(first_completed["iteration_index"])
        self.assertTrue(first_completed["parent_completed"])

        second_completed = appender.events[2][2]
        self.assertEqual(second_completed["instance_id"], "step-b-1")
        self.assertEqual(second_completed["outputs"], {"result": "b"})

    def test_partial_for_each_submission_records_only_addressed_instance(self):
        appender = SpyEventAppender()
        sut = OutputRecorder(event_appender=appender)
        instances = self._for_each_instances()

        sut.record(
            "/run/events.jsonl",
            instances,
            {"review-1": {"result": "Alpha result"}},
            "session-42",
        )

        self.assertEqual(
            [event_type for _, event_type, _ in appender.events],
            ["step_completed", "session_step_recorded"],
        )
        completion = appender.events[0][2]
        self.assertEqual(completion["iteration_index"], 0)
        self.assertEqual(completion["item"], "Alpha.swift")
        self.assertFalse(completion["parent_completed"])

    def test_complete_for_each_submission_marks_only_final_event_as_parent_complete(self):
        appender = SpyEventAppender()
        sut = OutputRecorder(event_appender=appender)
        instances = self._for_each_instances()

        sut.record(
            "/run/events.jsonl",
            instances,
            {
                "review-1": {"result": "Alpha result"},
                "review-2": {"result": "Beta result"},
            },
            "session-42",
        )

        completion_events = [
            payload
            for _, event_type, payload in appender.events
            if event_type == "step_completed"
        ]
        self.assertEqual(
            [event["parent_completed"] for event in completion_events],
            [False, True],
        )

    def test_no_instances_records_nothing(self):
        appender = SpyEventAppender()
        sut = OutputRecorder(event_appender=appender)

        sut.record("/run/events.jsonl", [], {}, "session-1")

        self.assertEqual(appender.events, [])

    def _for_each_instances(self) -> list[StepInstance]:
        return [
            StepInstance(
                step_id="review",
                instance_id="review-1",
                item="Alpha.swift",
                prompt="Review Alpha.swift",
                iteration_index=0,
            ),
            StepInstance(
                step_id="review",
                instance_id="review-2",
                item="Beta.swift",
                prompt="Review Beta.swift",
                iteration_index=1,
            ),
        ]


if __name__ == "__main__":
    unittest.main()
