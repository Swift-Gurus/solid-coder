"""Validates deterministic step conditions after runtime instance expansion."""

from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.comparison_condition import ComparisonCondition  # noqa: E402
from harness.condition_declaration import ConditionDeclaration  # noqa: E402
from harness.condition_operator import ConditionOperator  # noqa: E402
from harness.conditional_step_instance_expander import ConditionalStepInstanceExpander  # noqa: E402
from harness.models import RunState, StepDef, StepInstance  # noqa: E402


@dataclass
class StubStepInstanceExpander:
    instances: list[StepInstance]

    def expand(
        self,
        step: StepDef,
        context: dict[str, Any],
        run_state: RunState,
    ) -> list[StepInstance]:
        return self.instances


@dataclass
class StubConditionEvaluator:
    decisions: list[bool]
    contexts: list[dict[str, Any]] = field(default_factory=list)

    def evaluate(
        self,
        condition: ConditionDeclaration,
        context: dict[str, Any],
    ) -> bool:
        self.contexts.append(context)
        return self.decisions.pop(0)


class TestConditionalStepInstanceExpander(unittest.TestCase):

    def test_marks_each_false_expanded_instance_as_skipped(self) -> None:
        condition = ComparisonCondition(
            reference="{{item.language}}",
            operator=ConditionOperator.EQUALS,
            expected="swift",
        )
        instances = [
            StepInstance(
                step_id="review",
                instance_id="review-1",
                item={"language": "swift"},
                prompt="Review Swift",
                iteration_index=0,
            ),
            StepInstance(
                step_id="review",
                instance_id="review-2",
                item={"language": "kotlin"},
                prompt="Review Kotlin",
                iteration_index=1,
            ),
        ]
        evaluator = StubConditionEvaluator(decisions=[True, False])
        sut = ConditionalStepInstanceExpander(
            instance_expander=StubStepInstanceExpander(instances),
            condition_evaluator=evaluator,
        )

        result = sut.expand(
            StepDef(
                id="review",
                prompt="Review {{item.language}}",
                for_each="{{params.units}}",
                condition=condition,
            ),
            {"params": {"units": []}},
            RunState(completed={}, running=[], turn_count=0, status="in_progress"),
        )

        self.assertIsNone(result[0].skip)
        self.assertEqual(result[1].skip.condition, condition)
        self.assertEqual(result[1].skip.instance_id, "review-2")
        self.assertEqual(
            [context["item"] for context in evaluator.contexts],
            [{"language": "swift"}, {"language": "kotlin"}],
        )

    def test_omitted_condition_preserves_unconditional_instances(self) -> None:
        instance = StepInstance(
            step_id="review",
            instance_id="review-1",
            item=None,
            prompt="Review",
        )
        evaluator = StubConditionEvaluator(decisions=[])
        sut = ConditionalStepInstanceExpander(
            instance_expander=StubStepInstanceExpander([instance]),
            condition_evaluator=evaluator,
        )

        result = sut.expand(
            StepDef(id="review", prompt="Review"),
            {},
            RunState(completed={}, running=[], turn_count=0, status="in_progress"),
        )

        self.assertEqual(result, [instance])
        self.assertEqual(evaluator.contexts, [])


if __name__ == "__main__":
    unittest.main()
