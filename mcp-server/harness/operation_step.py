"""Defines one internal logical-operation step declaration."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.workflow_input_binding import WorkflowInputBinding


"""
solid-name: OperationStep
solid-category: model
solid-spec: [SPEC-010, SPEC-040]
solid-description: Carries a logical operation name and its typed workflow input bindings.
"""
@dataclass(frozen=True)
class OperationStep:
    name: str
    input_bindings: list[WorkflowInputBinding] = field(default_factory=list)
