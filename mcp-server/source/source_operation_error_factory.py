"""Constructs deterministic source-operation failures."""

from source.source_operation_error import SourceOperationError
from source.source_operation_error_creating import SourceOperationErrorCreating


"""
solid-name: SourceOperationErrorFactory
solid-category: factory
solid-spec: [SPEC-040]
solid-description: Constructs source-operation failures from contextual messages.
"""
class SourceOperationErrorFactory(SourceOperationErrorCreating):
    def create(self, message: str) -> SourceOperationError:
        return SourceOperationError(message)
