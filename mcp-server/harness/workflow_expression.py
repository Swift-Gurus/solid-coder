"""Defines one normalized workflow expression."""

from dataclasses import dataclass


"""
solid-name: WorkflowExpression
solid-category: model
solid-spec: [SPEC-037]
solid-description: Represents a normalized workflow-expression value.
"""
@dataclass(frozen=True)
class WorkflowExpression:
    value: str
