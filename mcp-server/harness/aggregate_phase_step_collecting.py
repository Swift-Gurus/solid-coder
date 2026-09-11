"""Declares aggregate phase step collection."""

from __future__ import annotations

from typing import Protocol

from harness.flow_def import FlowDef
from harness.run_state import RunState
from harness.step_def import StepDef


"""
solid-name: AggregatePhaseStepCollecting
solid-category: abstraction
solid-spec: [SPEC-045]
solid-description: Contract for collecting compatible model steps within one aggregate boundary.
"""
class AggregatePhaseStepCollecting(Protocol):
    def collect(
        self,
        flow: FlowDef,
        state: RunState,
        first: StepDef,
        boundary_id: str,
    ) -> list[str]: ...
