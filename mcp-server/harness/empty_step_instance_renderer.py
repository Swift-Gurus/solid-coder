"""Renders engine-completed instances for empty workflow collections."""

from __future__ import annotations

from harness.empty_step_instance_rendering import EmptyStepInstanceRendering
from harness.models import StepDef, StepInstance, StepOutputs


"""
solid-name: EmptyStepInstanceRenderer
solid-category: service
solid-spec: [SPEC-010, SPEC-030]
solid-description: Renders an empty workflow collection as an engine-completed instance with aggregate outputs.
"""
class EmptyStepInstanceRenderer(EmptyStepInstanceRendering):
    def render(self, step: StepDef) -> StepInstance:
        return StepInstance(
            step_id=step.id,
            instance_id=f"{step.id}-0",
            item=None,
            prompt="",
            iteration_index=0,
            automatic_outputs=StepOutputs(values={
                output.name: []
                for output in step.outputs
            }),
        )
