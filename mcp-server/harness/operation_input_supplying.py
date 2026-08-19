"""Defines the runtime input capability of an operation step instance."""

from typing import Protocol

from harness.workflow_context_values import WorkflowContextValues


"""
solid-name: OperationInputSupplying
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-040]
solid-description: Contract for supplying resolved operation input values.
"""
class OperationInputSupplying(Protocol):
    @property
    def inputs(self) -> WorkflowContextValues[object]: ...
