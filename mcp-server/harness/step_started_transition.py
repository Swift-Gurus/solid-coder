"""Applies a step-started event to reconstructed state."""


"""
solid-name: StepStartedTransition
solid-category: service
solid-spec: [SPEC-030]
solid-description: Marks a started workflow step as running when it is not already active.
"""
class StepStartedTransition:
    def apply(self, state: dict, event: dict) -> None:
        step_id = event.get("step_id", event.get("instance_id", ""))
        if step_id and step_id not in state["running"]:
            state["running"].append(step_id)
