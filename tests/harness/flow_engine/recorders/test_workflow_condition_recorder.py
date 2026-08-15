"""
solid-name: TestWorkflowConditionRecorder
solid-description: Validates durable event payloads for workflow-level condition decisions.
solid-category: unit-test
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.comparison_condition import ComparisonCondition
from harness.condition_operator import ConditionOperator
from harness.workflow_condition_decision import WorkflowConditionDecision
from harness.workflow_condition_recorder import WorkflowConditionRecorder


class SpyEventAppender:
    def __init__(self) -> None:
        self.calls = []

    def append(self, path, event_type, payload) -> None:
        self.calls.append((path, event_type, payload))


class StubConditionSerializer:
    def __init__(self, serialized: dict) -> None:
        self.serialized = serialized

    def serialize(self, condition) -> dict:
        return self.serialized


class TestWorkflowConditionRecorder(unittest.TestCase):

    def test_records_serialized_condition_and_match_result(self):
        appender = SpyEventAppender()
        serialized = {"ref": "{{params.enabled}}", "equals": True}
        sut = WorkflowConditionRecorder(
            event_appender=appender,
            condition_serializer=StubConditionSerializer(serialized),
        )
        decision = WorkflowConditionDecision(
            condition=ComparisonCondition(
                reference="{{params.enabled}}",
                operator=ConditionOperator.EQUALS,
                expected=True,
            ),
            matched=False,
        )

        sut.record("events.jsonl", decision)

        self.assertEqual(
            appender.calls,
            [
                (
                    "events.jsonl",
                    "workflow_condition_evaluated",
                    {"condition": serialized, "matched": False},
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()
