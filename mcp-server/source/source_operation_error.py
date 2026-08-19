"""Defines deterministic source-operation failures."""


"""
solid-name: SourceOperationError
solid-category: model
solid-spec: [SPEC-040]
solid-description: Reports a failed deterministic source operation with project context.
"""
class SourceOperationError(RuntimeError):
    pass
