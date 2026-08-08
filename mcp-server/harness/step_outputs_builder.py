"""Constructs recorded step output values."""

from __future__ import annotations

from typing import Any

from harness.step_outputs import StepOutputs


"""
solid-name: StepOutputsBuilder
solid-category: service
solid-spec: [SPEC-030]
solid-description: Constructs immutable recorded step outputs from submitted named values.
"""
class StepOutputsBuilder:
    def build(self, values: dict[str, Any]) -> StepOutputs:
        return StepOutputs(values=dict(values))
