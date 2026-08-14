"""Checks workflow-step status against reconstructed run state."""

from __future__ import annotations

from harness.models import RunState
from harness.step_status_checking import StepStatusChecking


"""
solid-name: StepStatusChecker
solid-category: service
solid-spec: [SPEC-010, SPEC-030]
solid-description: Determines whether a workflow step is completed or currently running.
"""
class StepStatusChecker(StepStatusChecking):
    def is_done_or_running(self, step_id: str, run_state: RunState) -> bool:
        return step_id in run_state.completed or step_id in run_state.running
