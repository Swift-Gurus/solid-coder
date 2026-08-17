"""Defines one parent-to-child workflow input expression."""

from dataclasses import dataclass

from harness.workflow_expression import WorkflowExpression


"""
solid-name: WorkflowInputBinding
solid-category: model
solid-spec: [SPEC-037]
solid-description: Associates one declared child workflow input with its parent-context expression.
"""
@dataclass(frozen=True)
class WorkflowInputBinding:
    name: str
    expression: WorkflowExpression
