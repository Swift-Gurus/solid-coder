"""
solid-name: FlowStartResultBuilding
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for assembling a FlowStartResult from a run's execution outcome.
"""

from __future__ import annotations

from typing import Protocol

from harness.execution_outcome import ExecutionOutcome
from harness.flow_start_result import FlowStartResult


class FlowStartResultBuilding(Protocol):
    def build(self, run_id: str, outcome: ExecutionOutcome, isolated: bool) -> FlowStartResult: ...
