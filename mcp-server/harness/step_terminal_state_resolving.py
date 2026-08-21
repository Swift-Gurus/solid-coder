"""Defines terminal-state resolution for workflow steps."""

from __future__ import annotations

from typing import Protocol

from harness.models import RunState
from harness.step_terminal_state import StepTerminalState


"""
solid-name: StepTerminalStateResolving
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for resolving a workflow step's completed, skipped, or pending state.
"""
class StepTerminalStateResolving(Protocol):
    def resolve(
        self,
        step_id: str,
        run_state: RunState,
    ) -> StepTerminalState: ...
