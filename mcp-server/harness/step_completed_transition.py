"""Applies a step-completed event to reconstructed state."""

from harness.step_outputs_building import StepOutputsBuilding


"""
solid-name: StepCompletedTransition
solid-category: service
solid-spec: [SPEC-030]
solid-description: Records validated step outputs and removes the completed step from active execution.
"""
class StepCompletedTransition:

    def __init__(self, step_outputs_builder: StepOutputsBuilding) -> None:
        self._step_outputs_builder = step_outputs_builder

    def apply(self, state: dict, event: dict) -> None:
        step_id = event.get("step_id", event.get("instance_id", ""))
        state["completed"][step_id] = self._step_outputs_builder.build(event.get("outputs") or {})
        if step_id in state["running"]:
            state["running"].remove(step_id)
