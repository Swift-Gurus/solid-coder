"""Constructs exhausted-attempt diagnostics."""

from __future__ import annotations

from harness.attempt_exhaustion_message_building import AttemptExhaustionMessageBuilding
from harness.exhausted_attempt import ExhaustedAttempt
from harness.models import RunState


"""
solid-name: AttemptExhaustionMessageBuilder
solid-category: service
solid-spec: [SPEC-010, SPEC-031]
solid-description: Constructs an actionable diagnostic for an exhausted workflow execution attempt.
"""
class AttemptExhaustionMessageBuilder(AttemptExhaustionMessageBuilding):
    def build(
        self,
        exhausted: ExhaustedAttempt,
        run_state: RunState,
        events_path: str,
    ) -> str:
        attempts = run_state.attempts_used.get(exhausted.attempt_id, 0)
        reason = run_state.rejection_reasons.get(
            exhausted.attempt_id,
            "unknown reason",
        )
        target = f"step '{exhausted.step_id}'"
        if exhausted.attempt_id != exhausted.step_id:
            target += f" instance '{exhausted.attempt_id}'"
        return (
            f"Flow failed — {target} exhausted all {attempts} attempt(s). Last rejection: {reason}. "
            f"Full run log: {events_path}. Stop here — do not retry or continue this flow. Report this failure "
            "to the user and wait for their instructions."
        )
