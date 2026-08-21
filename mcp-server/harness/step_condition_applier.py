"""Applies a condition decision to one workflow-step instance."""

from __future__ import annotations

from dataclasses import replace

from harness.condition_decision_evaluating import ConditionDecisionEvaluating
from harness.condition_declaration import ConditionDeclaration
from harness.models import StepInstance
from harness.step_condition_applying import StepConditionApplying
from harness.step_skip import StepSkip
from harness.workflow_run_context import WorkflowRunContext
from harness.workflow_step_context_resolving import WorkflowStepContextResolving


"""
solid-name: StepConditionApplier
solid-category: service
solid-spec: [SPEC-037]
solid-description: Applies deterministic workflow-condition policy to one expanded step instance.
"""
class StepConditionApplier(StepConditionApplying):

    def __init__(
        self,
        condition_evaluator: ConditionDecisionEvaluating,
        context_resolver: WorkflowStepContextResolving,
    ) -> None:
        self._condition_evaluator = condition_evaluator
        self._context_resolver = context_resolver

    def apply(
        self,
        instance: StepInstance,
        condition: ConditionDeclaration,
        item: object,
        context: WorkflowRunContext,
    ) -> StepInstance:
        if instance.automatic_outputs is not None:
            return instance
        condition_context = self._context_resolver.resolve(
            context,
            instance.workflow_instance,
            item,
        )
        evidence = self._condition_evaluator.evaluate(
            condition,
            condition_context,
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
                item=item,
                iteration_index=instance.iteration_index,
            ),
        )
