"""Defines durable serialization of normalized workflow expressions."""

from typing import Protocol

from harness.workflow_expression import WorkflowExpression


"""
solid-name: WorkflowExpressionSerializing
solid-category: abstraction
solid-spec: [SPEC-037, SPEC-040]
solid-description: Contract for serializing normalized workflow expressions into public YAML values.
"""
class WorkflowExpressionSerializing(Protocol):
    def serialize(self, expression: WorkflowExpression) -> str: ...
