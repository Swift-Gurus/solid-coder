"""Validates workflow conditions are applied before instance rendering."""

from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.comparison_condition import ComparisonCondition
from harness.comparison_condition_evidence import ComparisonConditionEvidence
from harness.condition_declaration import ConditionDeclaration
from harness.condition_evidence import ConditionEvidence
from harness.condition_operator import ConditionOperator
from harness.conditional_step_instance_builder import ConditionalStepInstanceBuilder
from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.models import StepDef, StepInstance
from harness.resolved_condition_value import ResolvedConditionValue
from harness.step_condition_applier import StepConditionApplier
from harness.workflow_expression import WorkflowExpression
from harness.workflow_context_value import WorkflowContextValue
from harness.workflow_context_values import WorkflowContextValues
from harness.workflow_run_context import WorkflowRunContext
from harness.workflow_step_context_resolver import WorkflowStepContextResolver


@dataclass
class StubInstanceBuilder:
    calls: list[object] = field(default_factory=list)

    def build(
        self,
        step: StepDef,
        context: WorkflowRunContext,
        item: object,
        instance_id: str,
        iteration_index: int | None = None,
    ) -> StepInstance:
        self.calls.append(item)
        return StepInstance(
            step_id=step.id,
            instance_id=instance_id,
            item=item,
            prompt="Rendered",
            iteration_index=iteration_index,
            workflow_instance=step.workflow_instance,
        )


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


class TestConditionalStepInstanceBuilder(unittest.TestCase):

    def test_false_include_condition_skips_without_rendering(self) -> None:
        condition = self._condition()
        source_item = {"file_extension": ".md"}
        child_inputs = WorkflowContextValues(entries=[
            WorkflowContextValue(name="review_unit", value=source_item),
        ])
        delegate = StubInstanceBuilder()
        evaluator = StubConditionEvaluator([
            self._evidence(actual=".md", matched=False)
        ])
        sut = ConditionalStepInstanceBuilder(
            delegate=delegate,
            condition_applier=StepConditionApplier(
                evaluator,
                WorkflowStepContextResolver(),
            ),
        )
        step = StepDef(
            id="review.inspect",
            prompt="{{steps.parent.outputs.value}}",
            workflow_instance=IncludedWorkflowInstance(
                alias="review",
                instance_id="review-1",
                source_index=0,
                source_item=source_item,
                condition=condition,
                inputs=child_inputs,
            ),
        )

        result = sut.build(
            step,
            WorkflowRunContext(),
            None,
            "review.inspect-1",
        )

        self.assertEqual(delegate.calls, [])
        self.assertEqual(result.prompt, "")
        self.assertEqual(result.skip.condition, condition)
        self.assertEqual(result.skip.item, source_item)
        self.assertEqual(evaluator.contexts[0].item.value, source_item)
        self.assertEqual(evaluator.contexts[0].parameters, child_inputs)

    def test_matching_condition_delegates_to_the_renderer(self) -> None:
        delegate = StubInstanceBuilder()
        evaluator = StubConditionEvaluator([
            self._evidence(actual=".swift", matched=True)
        ])
        sut = ConditionalStepInstanceBuilder(
            delegate=delegate,
            condition_applier=StepConditionApplier(
                evaluator,
                WorkflowStepContextResolver(),
            ),
        )
        item = {"file_extension": ".swift"}

        result = sut.build(
            StepDef(
                id="review",
                prompt="Review",
                condition=self._condition(),
            ),
            WorkflowRunContext(),
            item,
            "review-1",
        )

        self.assertEqual(result.prompt, "Rendered")
        self.assertEqual(delegate.calls, [item])

    def _condition(self) -> ComparisonCondition:
        return ComparisonCondition(
            reference=WorkflowExpression("item.file_extension"),
            operator=ConditionOperator.EQUALS,
            expected=".swift",
        )

    def _evidence(
        self,
        actual: str,
        matched: bool,
    ) -> ComparisonConditionEvidence:
        return ComparisonConditionEvidence(
            reference="item.file_extension",
            operator=ConditionOperator.EQUALS,
            expected=".swift",
            actual=ResolvedConditionValue(present=True, value=actual),
            matched=matched,
        )


if __name__ == "__main__":
    unittest.main()
