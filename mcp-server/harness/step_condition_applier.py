"""Applies a condition decision to one workflow-step instance."""

from __future__ import annotations

from dataclasses import replace

from harness.condition_decision_evaluating import ConditionDecisionEvaluating
from harness.models import StepDef, StepInstance
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
        step: StepDef,
        instance: StepInstance,
        context: WorkflowRunContext,
    ) -> StepInstance:
        if instance.automatic_outputs is not None:
            return instance
        workflow_instance = instance.workflow_instance
        item = (
            workflow_instance.source_item
            if workflow_instance is not None
            else instance.item
        )
        conditions = []
        if workflow_instance is not None and workflow_instance.condition is not None:
            conditions.append(workflow_instance.condition)
        if step.condition is not None:
            conditions.append(step.condition)

        condition_context = self._context_resolver.resolve(
            context,
            workflow_instance,
            item,
        )
        for condition in conditions:
            evidence = self._condition_evaluator.evaluate(
                condition,
                condition_context,
            )
            if not evidence.matched:
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
        return instance
