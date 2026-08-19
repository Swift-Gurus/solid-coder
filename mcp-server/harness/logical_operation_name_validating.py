"""Defines validation of transport-independent operation names."""

from typing import Protocol


"""
solid-name: LogicalOperationNameValidating
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-040]
solid-description: Contract for validating transport-independent logical operation names.
"""
class LogicalOperationNameValidating(Protocol):
    def is_valid(self, name: str) -> bool: ...
