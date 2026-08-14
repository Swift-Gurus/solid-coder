"""Defines one durably completed iteration of a workflow step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from harness.step_outputs import StepOutputs


"""
solid-name: StepInstanceCompletion
solid-category: model
solid-spec: [SPEC-010, SPEC-030]
solid-description: Records the identity, item binding, and validated outputs of one completed for-each iteration.
"""
@dataclass(frozen=True)
class StepInstanceCompletion:
    step_id: str
    instance_id: str
    iteration_index: int
    item: Any
    outputs: StepOutputs
