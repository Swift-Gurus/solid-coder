"""Defines the workflow definition validation failure."""


"""
solid-name: FlowValidationError
solid-category: model
solid-spec: [SPEC-030, SPEC-027, SPEC-035]
solid-description: Represents an actionable failure to resolve or validate a workflow definition.
"""
class FlowValidationError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
