"""Applies typed conditions after workflow-step instance expansion."""

from __future__ import annotations

from harness.models import RunState, StepDef, StepInstance
from harness.step_condition_applying import StepConditionApplying
from harness.step_instance_expanding import StepInstanceExpanding
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: ConditionalStepInstanceExpander
solid-category: service
solid-spec: [SPEC-037]
solid-description: Applies a step condition independently to each expanded workflow instance.
"""
class ConditionalStepInstanceExpander(StepInstanceExpanding):
    def __init__(
        self,
        instance_expander: StepInstanceExpanding,
        condition_applier: StepConditionApplying,
    ) -> None:
        self._instance_expander = instance_expander
        self._condition_applier = condition_applier

    def expand(
        self,
        step: StepDef,
        context: WorkflowRunContext,
        run_state: RunState,
    ) -> list[StepInstance]:
        instances = self._instance_expander.expand(step, context, run_state)
        if step.condition is None:
            return instances
        return [
            self._condition_applier.apply(step, instance, context)
            for instance in instances
        ]
