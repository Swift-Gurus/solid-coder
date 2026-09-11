"""Declares aggregate phase instance materialization."""

from typing import Protocol

from harness.aggregate_phase import AggregatePhase
from harness.flow_def import FlowDef
from harness.step_instance import StepInstance


"""
solid-name: AggregatePhaseMaterializing
solid-category: abstraction
solid-spec: [SPEC-045]
solid-description: Contract for materializing one planned aggregate phase as original workflow-step instances.
"""
class AggregatePhaseMaterializing(Protocol):
    def materialize(
        self,
        flow: FlowDef,
        phase: AggregatePhase,
        seed: StepInstance,
    ) -> list[StepInstance]: ...
