"""Defines one resolved child-workflow input value."""

from dataclasses import dataclass


"""
solid-name: ResolvedWorkflowInput
solid-category: model
solid-spec: [SPEC-037]
solid-description: Associates one child workflow input name with its resolved runtime value.
"""
@dataclass(frozen=True)
class ResolvedWorkflowInput:
    name: str
    value: object
