"""Declares aggregate expansion of a ready model frontier."""

from typing import Protocol

from harness.flow_def import FlowDef
from harness.run_state import RunState
from harness.step_instance import StepInstance


"""
solid-name: AggregateReadyStepExpanding
solid-category: abstraction
solid-spec: [SPEC-045]
solid-description: Contract for expanding aggregate phases over an existing ready workflow frontier.
"""
class AggregateReadyStepExpanding(Protocol):
    def expand(
        self,
        flow: FlowDef,
        state: RunState,
        ready: list[StepInstance],
    ) -> list[StepInstance]: ...
