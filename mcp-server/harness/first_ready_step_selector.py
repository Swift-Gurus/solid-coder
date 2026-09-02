"""Selects the first queued ready step for model presentation."""

from __future__ import annotations

from harness.ready_step_selecting import ReadyStepSelecting
from harness.step_result import StepResult


"""
solid-name: FirstReadyStepSelector
solid-category: service
solid-spec: [SPEC-031]
solid-description: Selects only the first engine-ordered ready step for the current model turn.
"""
class FirstReadyStepSelector(ReadyStepSelecting):
    def select(self, steps: list[StepResult]) -> StepResult | None:
        return steps[0] if steps else None
