"""Evaluates workflow attempt budgets."""

from __future__ import annotations

from harness.attempt_exhaustion_evaluating import AttemptExhaustionEvaluating
from harness.exhausted_attempt import ExhaustedAttempt
from harness.models import FlowDef, RunState


"""
solid-name: AttemptExhaustionEvaluator
solid-category: service
solid-spec: [SPEC-010, SPEC-031]
solid-description: Identifies an execution identity that exhausted its declared workflow-step attempt budget.
"""
class AttemptExhaustionEvaluator(AttemptExhaustionEvaluating):
    def evaluate(
        self,
        flow_def: FlowDef,
        run_state: RunState,
    ) -> ExhaustedAttempt | None:
        for attempt_id, attempts in run_state.attempts_used.items():
            step_id = run_state.attempt_step_ids.get(attempt_id, attempt_id)
            if step_id in run_state.completed:
                continue
            step = next(
                (candidate for candidate in flow_def.steps if candidate.id == step_id),
                None,
            )
            if step is not None and attempts >= step.max_attempts:
                return ExhaustedAttempt(attempt_id=attempt_id, step_id=step_id)
        return None
