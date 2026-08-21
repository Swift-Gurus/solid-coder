"""Resolves terminal workflow-step state from replayed run state."""

from __future__ import annotations

from harness.models import RunState
from harness.step_terminal_state import StepTerminalState
from harness.step_terminal_state_resolving import StepTerminalStateResolving


"""
solid-name: StepTerminalStateResolver
solid-category: service
solid-spec: [SPEC-037]
solid-description: Resolves a workflow step's completed, skipped, or pending state.
"""
class StepTerminalStateResolver(StepTerminalStateResolving):
    def resolve(
        self,
        step_id: str,
        run_state: RunState,
    ) -> StepTerminalState:
        if step_id in run_state.completed:
            return StepTerminalState.COMPLETED
        if step_id in run_state.skipped:
            return StepTerminalState.SKIPPED
        return StepTerminalState.PENDING
