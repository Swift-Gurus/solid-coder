"""
solid-description: Represents the outcome of a submission action that determines whether the run continues or terminates.
solid-category: model
"""

from __future__ import annotations

from dataclasses import dataclass

from harness.flow_next_result import FlowNextResult
from harness.models import RunState


@dataclass(frozen=True)
class SubmissionOutcome:
    run_state: RunState | None = None
    terminal: FlowNextResult | None = None
