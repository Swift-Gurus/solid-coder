"""
solid-description: Contract for checking whether a workflow step is ready to execute.
solid-category: abstraction
"""

from __future__ import annotations

from typing import Protocol

from harness.models import RunState, StepDef


class StepReadinessChecking(Protocol):
    """
    solid-description: Contract for determining whether a workflow step is ready to proceed.
    solid-category: abstraction
    """

    def is_done_or_running(self, step_id: str, run_state: RunState) -> bool: ...
    def dependencies_met(self, step: StepDef, run_state: RunState) -> bool: ...