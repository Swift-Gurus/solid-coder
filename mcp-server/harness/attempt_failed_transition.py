"""Applies a failed-attempt event to reconstructed state."""


"""
solid-name: AttemptFailedTransition
solid-category: service
solid-spec: [SPEC-027]
solid-description: Records a step attempt and its latest rejection reason in reconstructed run state.
"""
class AttemptFailedTransition:
    def apply(self, state: dict, event: dict) -> None:
        step_id = event.get("step_id", "")
        state["attempts_used"][step_id] = state["attempts_used"].get(step_id, 0) + 1
        state["rejection_reasons"][step_id] = event.get("reason", "")
