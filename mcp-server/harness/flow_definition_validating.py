"""Defines validation of resolved and assembled workflow definitions."""

from typing import Protocol

from harness.flow_def import FlowDef


"""
solid-name: FlowDefinitionValidating
solid-category: abstraction
solid-spec: [SPEC-030, SPEC-035]
solid-description: Contract for validating resolved workflow structure and final executable references.
"""
class FlowDefinitionValidating(Protocol):

    def validate_resolved(self, definition: FlowDef) -> None:
        ...

    def validate_assembled(self, flow: FlowDef) -> None:
        ...
