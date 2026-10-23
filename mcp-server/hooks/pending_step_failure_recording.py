"""
solid-name: PendingStepFailureRecording
solid-category: abstraction
solid-tags: [hook]
solid-description: Contract for recording a failed attempt against a run's pending step.
"""

from __future__ import annotations

from typing import Protocol

from harness.flow_next_result import FlowNextResult


class PendingStepFailureRecording(Protocol):
    def record(self, run_id: str | None, step_id: str) -> FlowNextResult | None: ...
