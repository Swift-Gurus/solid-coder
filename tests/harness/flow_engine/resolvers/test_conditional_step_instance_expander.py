"""Validates deterministic step conditions after runtime instance expansion."""

from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.comparison_condition import ComparisonCondition  # noqa: E402
from harness.comparison_condition_evidence import ComparisonConditionEvidence  # noqa: E402
from harness.condition_declaration import ConditionDeclaration  # noqa: E402
from harness.condition_evidence import ConditionEvidence  # noqa: E402
from harness.condition_operator import ConditionOperator  # noqa: E402
from harness.conditional_step_instance_expander import ConditionalStepInstanceExpander  # noqa: E402
from harness.included_workflow_instance import IncludedWorkflowInstance  # noqa: E402
from harness.models import RunState, StepDef, StepInstance  # noqa: E402
from harness.resolved_condition_value import ResolvedConditionValue  # noqa: E402
from harness.step_condition_applier import StepConditionApplier  # noqa: E402
from harness.workflow_run_context import WorkflowRunContext  # noqa: E402
from harness.workflow_expression import WorkflowExpression  # noqa: E402


@dataclass
class StubStepInstanceExpander:
    instances: list[StepInstance]

    def expand(
        self,
        step: StepDef,
        context: WorkflowRunContext,
        run_state: RunState,
    ) -> list[StepInstance]:
        return self.instances


@dataclass
class StubConditionEvaluator:
    decisions: list[ConditionEvidence]
    contexts: list[WorkflowRunContext] = field(default_factory=list)

    def evaluate(
        self,
        condition: ConditionDeclaration,
        context: WorkflowRunContext,
    ) -> ConditionEvidence:
        self.contexts.append(context)
        return self.decisions.pop(0)


class TestConditionalStepInstanceExpander(unittest.TestCase):

    def test_marks_each_false_expanded_instance_as_skipped(self) -> None:
        condition = ComparisonCondition(
            reference=WorkflowExpression(value="item.language"),
            operator=ConditionOperator.EQUALS,
            expected="swift",
        )
        workflow_instance = IncludedWorkflowInstance(
            alias="review",
            instance_id="review-2",
            source_index=1,
            source_item={"language": "kotlin"},
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
                workflow_instance=workflow_instance,
            ),
        ]
        matching = self._evidence(actual="swift", matched=True)
        skipped = self._evidence(actual="kotlin", matched=False)
        evaluator = StubConditionEvaluator(decisions=[matching, skipped])
        sut = ConditionalStepInstanceExpander(
            instance_expander=StubStepInstanceExpander(instances),
            condition_applier=StepConditionApplier(evaluator),
        )

        result = sut.expand(
            StepDef(
                id="review",
                prompt="Review {{item.language}}",
                for_each="{{params.units}}",
                condition=condition,
            ),
            WorkflowRunContext(),
            RunState(completed={}, running=[], turn_count=0, status="in_progress"),
        )

        self.assertIsNone(result[0].skip)
        self.assertEqual(result[1].skip.condition, condition)
        self.assertEqual(result[1].skip.instance_id, "review-2")
        self.assertEqual(result[1].skip.evidence, skipped)
        self.assertEqual(result[1].workflow_instance, workflow_instance)
        self.assertEqual(
            [context.item.value for context in evaluator.contexts],
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
            condition_applier=StepConditionApplier(evaluator),
        )

        result = sut.expand(
            StepDef(id="review", prompt="Review"),
            WorkflowRunContext(),
            RunState(completed={}, running=[], turn_count=0, status="in_progress"),
        )

        self.assertEqual(result, [instance])
        self.assertEqual(evaluator.contexts, [])

    def _evidence(
        self,
        actual: str,
        matched: bool,
    ) -> ComparisonConditionEvidence:
        return ComparisonConditionEvidence(
            reference="item.language",
            operator=ConditionOperator.EQUALS,
            expected="swift",
            actual=ResolvedConditionValue(present=True, value=actual),
            matched=matched,
        )


if __name__ == "__main__":
    unittest.main()
