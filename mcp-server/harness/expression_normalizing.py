"""Defines normalization of a workflow expression wrapper."""

from typing import Protocol


"""
solid-name: ExpressionNormalizing
solid-category: abstraction
solid-spec: [SPEC-030, SPEC-037]
solid-description: Contract for normalizing a workflow expression before evaluation.
"""
class ExpressionNormalizing(Protocol):
    def normalize(self, expression: str) -> str: ...
