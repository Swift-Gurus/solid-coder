"""Validates durable recording of conditionally skipped step instances."""

from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.all_condition_serializer import AllConditionSerializer  # noqa: E402
from harness.any_condition_serializer import AnyConditionSerializer  # noqa: E402
from harness.comparison_condition import ComparisonCondition  # noqa: E402
from harness.comparison_condition_serializer import ComparisonConditionSerializer  # noqa: E402
from harness.condition_operator import ConditionOperator  # noqa: E402
from harness.condition_serializer import ConditionSerializer  # noqa: E402
from harness.not_condition_serializer import NotConditionSerializer  # noqa: E402
from harness.step_instance import StepInstance  # noqa: E402
from harness.step_skip import StepSkip  # noqa: E402
from harness.step_skip_recorder import StepSkipRecorder  # noqa: E402
from harness.unsupported_condition_serializer import UnsupportedConditionSerializer  # noqa: E402


@dataclass
class SpyEventAppender:
    events: list[tuple[str, str, dict]] = field(default_factory=list)

    def append(self, path: str, event_type: str, payload: dict) -> None:
        self.events.append((path, event_type, payload))


class TestStepSkipRecorder(unittest.TestCase):

    def setUp(self) -> None:
        self.appender = SpyEventAppender()
        self.sut = StepSkipRecorder(
            event_appender=self.appender,
            condition_serializer=ConditionSerializer(
                comparison_serializer=ComparisonConditionSerializer(),
                all_serializer=AllConditionSerializer(),
                any_serializer=AnyConditionSerializer(),
                not_serializer=NotConditionSerializer(),
                fallback_serializer=UnsupportedConditionSerializer(),
            ),
        )
        self.condition = ComparisonCondition(
            reference="{{item.language}}",
            operator=ConditionOperator.EQUALS,
            expected="swift",
        )

    def test_all_skipped_instances_complete_parent_on_final_skip(self) -> None:
        ready = [self._instance(1, skipped=True), self._instance(2, skipped=True)]

        self.sut.record("/run/events.jsonl", ready)

        self.assertEqual(
            [event_type for _, event_type, _ in self.appender.events],
            ["step_skipped", "step_skipped"],
        )
        self.assertEqual(
            [payload["parent_completed"] for _, _, payload in self.appender.events],
            [False, True],
        )
        self.assertEqual(
            self.appender.events[0][2]["condition"],
            {"ref": "{{item.language}}", "equals": "swift"},
        )

    def test_mixed_instances_leave_parent_completion_to_executable_sibling(self) -> None:
        ready = [self._instance(1, skipped=True), self._instance(2, skipped=False)]

        self.sut.record("/run/events.jsonl", ready)

        self.assertEqual(len(self.appender.events), 1)
        self.assertFalse(self.appender.events[0][2]["parent_completed"])

    def _instance(self, index: int, skipped: bool) -> StepInstance:
        instance_id = f"review-{index}"
        return StepInstance(
            step_id="review",
            instance_id=instance_id,
            item={"language": "kotlin" if skipped else "swift"},
            prompt="Review",
            iteration_index=index - 1,
            skip=(
                StepSkip(
                    step_id="review",
                    instance_id=instance_id,
                    condition=self.condition,
                    item={"language": "kotlin"},
                    iteration_index=index - 1,
                )
                if skipped
                else None
            ),
        )


if __name__ == "__main__":
    unittest.main()
