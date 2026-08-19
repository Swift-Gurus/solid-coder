"""Defines construction of source-operation failures."""

from typing import Protocol

from source.source_operation_error import SourceOperationError


"""
solid-name: SourceOperationErrorCreating
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for constructing deterministic source-operation failures.
"""
class SourceOperationErrorCreating(Protocol):
    def create(self, message: str) -> SourceOperationError: ...
