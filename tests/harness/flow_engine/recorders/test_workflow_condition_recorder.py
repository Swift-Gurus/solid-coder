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
from harness.comparison_condition_evidence import ComparisonConditionEvidence
from harness.condition_operator import ConditionOperator
from harness.resolved_condition_value import ResolvedConditionValue
from harness.workflow_condition_decision import WorkflowConditionDecision
from harness.workflow_condition_recorder import WorkflowConditionRecorder
from harness.workflow_expression import WorkflowExpression


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
                reference=WorkflowExpression(value="params.enabled"),
                operator=ConditionOperator.EQUALS,
                expected=True,
            ),
            evidence=ComparisonConditionEvidence(
                reference="params.enabled",
                operator=ConditionOperator.EQUALS,
                expected=True,
                actual=ResolvedConditionValue(present=True, value=False),
                matched=False,
            ),
        )

        sut.record("events.jsonl", decision)

        self.assertEqual(
            appender.calls,
            [
                (
                    "events.jsonl",
                    "workflow_condition_evaluated",
                    {
                        "condition": serialized,
                        "matched": False,
                        "evidence": {
                            "kind": "comparison",
                            "reference": "params.enabled",
                            "operator": "equals",
                            "expected": True,
                            "actual": {"present": True, "value": False},
                            "matched": False,
                        },
                    },
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()
