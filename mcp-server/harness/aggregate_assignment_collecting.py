"""Declares aggregate assignment collection from ready results."""

from typing import Protocol

from harness.aggregate_assignment import AggregateAssignment
from harness.step_result import StepResult


"""
solid-name: AggregateAssignmentCollecting
solid-category: abstraction
solid-spec: [SPEC-045]
solid-description: Contract for collecting model-ready aggregate assignments from original step results.
"""
class AggregateAssignmentCollecting(Protocol):
    def collect(self, steps: list[StepResult]) -> list[AggregateAssignment]: ...
