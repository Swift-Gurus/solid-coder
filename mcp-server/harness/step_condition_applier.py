"""Applies a condition decision to one workflow-step instance."""

from __future__ import annotations

from dataclasses import replace

from harness.condition_decision_evaluating import ConditionDecisionEvaluating
from harness.models import StepDef, StepInstance
from harness.resolved_workflow_context_value import ResolvedWorkflowContextValue
from harness.step_condition_applying import StepConditionApplying
from harness.step_skip import StepSkip
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: StepConditionApplier
solid-category: service
solid-spec: [SPEC-037]
solid-description: Applies deterministic workflow-condition policy to one expanded step instance.
"""
class StepConditionApplier(StepConditionApplying):

    def __init__(self, condition_evaluator: ConditionDecisionEvaluating) -> None:
        self._condition_evaluator = condition_evaluator

    def apply(
        self,
        step: StepDef,
        instance: StepInstance,
        context: WorkflowRunContext,
    ) -> StepInstance:
        condition = step.condition
        if instance.automatic_outputs is not None or condition is None:
            return instance
        evidence = self._condition_evaluator.evaluate(
            condition,
            replace(
                context,
                item=ResolvedWorkflowContextValue(
                    present=True,
                    value=instance.item,
                ),
            ),
        )
        if evidence.matched:
            return instance
        return replace(
            instance,
            skip=StepSkip(
                step_id=instance.step_id,
                instance_id=instance.instance_id,
                condition=condition,
                evidence=evidence,
                item=instance.item,
                iteration_index=instance.iteration_index,
            ),
        )
