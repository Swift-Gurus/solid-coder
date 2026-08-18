"""Defines collection of validated outputs from an executable review rule."""

from typing import Protocol

from harness.flow_def import FlowDef
from harness.rule_observations import RuleObservations
from harness.run_state import RunState


"""
solid-name: RuleObservationCollecting
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for collecting a rule's validated outputs into typed observations.
"""
class RuleObservationCollecting(Protocol):
    def collect(
        self,
        flow_def: FlowDef,
        run_state: RunState,
    ) -> RuleObservations: ...
