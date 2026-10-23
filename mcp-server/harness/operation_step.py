"""Defines one internal logical-operation step declaration."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.workflow_context_value import WorkflowContextValue
from harness.workflow_input_binding import WorkflowInputBinding

"""
solid-name: OperationStep
solid-category: model
solid-spec: [SPEC-010, SPEC-040]
solid-description: Carries a logical operation name, runtime input references, and fixed input values.
"""


@dataclass(frozen=True)
class OperationStep:
    name: str
    input_bindings: list[WorkflowInputBinding] = field(default_factory=list)
    input_values: list[WorkflowContextValue[object]] = field(default_factory=list)
