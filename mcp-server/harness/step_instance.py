"""Defines one ready execution of a workflow step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from harness.step_outputs import StepOutputs


"""
solid-name: StepInstance
solid-category: model
solid-spec: [SPEC-030]
solid-description: Represents a ready step execution with its instance identity, item binding, and rendered prompt.
"""
@dataclass(frozen=True)
class StepInstance:
    step_id: str
    instance_id: str
    item: Any
    prompt: str
    iteration_index: int | None = None
    automatic_outputs: StepOutputs | None = None

    @property
    def is_for_each(self) -> bool:
        return self.iteration_index is not None
