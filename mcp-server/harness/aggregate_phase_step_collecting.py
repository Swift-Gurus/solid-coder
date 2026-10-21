"""Declares aggregate phase step collection."""

from __future__ import annotations

from typing import Protocol

from harness.aggregate_phase import AggregatePhase
from harness.flow_def import FlowDef
from harness.run_state import RunState
from harness.step_def import StepDef
from harness.step_instance import StepInstance


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
        ready: list[StepInstance],
    ) -> AggregatePhase: ...
