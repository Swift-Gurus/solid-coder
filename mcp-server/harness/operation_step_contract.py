"""Defines the decoded operation step and its registered output contract."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.operation_step import OperationStep
from harness.output_spec import OutputSpec


"""
solid-name: OperationStepContract
solid-category: model
solid-spec: [SPEC-010, SPEC-040]
solid-description: Carries one decoded logical operation step and its registered outputs.
"""
@dataclass(frozen=True)
class OperationStepContract:
    step: OperationStep | None = None
    outputs: list[OutputSpec] = field(default_factory=list)
