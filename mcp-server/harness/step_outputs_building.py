"""Defines construction of recorded step output values."""

from __future__ import annotations

from typing import Any, Protocol

from harness.step_outputs import StepOutputs


"""
solid-name: StepOutputsBuilding
solid-category: abstraction
solid-spec: [SPEC-030]
solid-description: Contract for constructing recorded step outputs from named values.
"""
class StepOutputsBuilding(Protocol):
    def build(self, values: dict[str, Any]) -> StepOutputs: ...
