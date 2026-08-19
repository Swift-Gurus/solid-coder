"""Applies workflow conditions before rendering step instances."""

from __future__ import annotations

from harness.models import StepDef, StepInstance
from harness.step_condition_applying import StepConditionApplying
from harness.step_instance_building import StepInstanceBuilding
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: ConditionalStepInstanceBuilder
solid-category: decorator
solid-spec: [SPEC-037]
solid-description: Prevents ineligible workflow instances from rendering prompts or starting execution.
"""
class ConditionalStepInstanceBuilder:

    def __init__(
        self,
        delegate: StepInstanceBuilding,
        condition_applier: StepConditionApplying,
    ) -> None:
        self._delegate = delegate
        self._condition_applier = condition_applier

    def build(
        self,
        step: StepDef,
        context: WorkflowRunContext,
        item: object,
        instance_id: str,
        iteration_index: int | None = None,
    ) -> StepInstance:
        workflow_instance = step.workflow_instance
        source_item = (
            workflow_instance.source_item
            if workflow_instance is not None
            else item
        )
        unrendered = StepInstance(
            step_id=step.id,
            instance_id=instance_id,
            item=source_item,
            prompt="",
            iteration_index=iteration_index,
            workflow_instance=workflow_instance,
        )
        conditioned = self._condition_applier.apply(
            step,
            unrendered,
            context,
        )
        if conditioned.skip is not None:
            return conditioned
        return self._delegate.build(
            step,
            context,
            source_item,
            instance_id,
            iteration_index,
        )
