"""Defines aggregation of completed workflow iterations."""

from __future__ import annotations

from typing import Protocol

from harness.step_instance_completion import StepInstanceCompletion
from harness.step_outputs import StepOutputs


"""
solid-name: StepInstanceOutputAggregating
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-030]
solid-description: Contract for combining ordered workflow iteration results into parent-step outputs.
"""
class StepInstanceOutputAggregating(Protocol):
    def aggregate(self, completions: list[StepInstanceCompletion]) -> StepOutputs: ...
