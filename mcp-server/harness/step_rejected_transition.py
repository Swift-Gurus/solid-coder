"""Applies a rejected-step event to reconstructed state."""

from harness.run_state_transitioning import RunStateTransitioning


"""
solid-name: StepRejectedTransition
solid-category: service
solid-spec: [SPEC-027]
solid-description: Records a failed attempt and reopens the rejected completed step for another execution.
"""
class StepRejectedTransition:

    def __init__(self, attempt_transition: RunStateTransitioning) -> None:
        self._attempt_transition = attempt_transition

    def apply(self, state: dict, event: dict) -> None:
        self._attempt_transition.apply(state, event)
        state["completed"].pop(event.get("step_id", ""), None)
