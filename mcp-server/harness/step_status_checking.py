"""Defines workflow-step status checking."""

from __future__ import annotations

from typing import Protocol

from harness.models import RunState


"""
solid-name: StepStatusChecking
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-030]
solid-description: Contract for checking whether a workflow step is completed or currently running.
"""
class StepStatusChecking(Protocol):
    def is_done_or_running(self, step_id: str, run_state: RunState) -> bool: ...
