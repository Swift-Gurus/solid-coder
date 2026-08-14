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
        attempt_id = event.get("attempt_id") or step_id
        state["attempts_used"][attempt_id] = state["attempts_used"].get(attempt_id, 0) + 1
        state.setdefault("attempt_step_ids", {})[attempt_id] = step_id
        state["rejection_reasons"][attempt_id] = event.get("reason", "")
