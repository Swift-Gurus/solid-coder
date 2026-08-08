"""Creates workflow validation failures."""

from harness.flow_validation_error import FlowValidationError


"""
solid-name: FlowValidationErrorFactory
solid-category: service
solid-spec: [SPEC-030, SPEC-035]
solid-description: Creates an actionable workflow validation failure from a supplied message.
"""
class FlowValidationErrorFactory:
    def create(self, message: str) -> FlowValidationError:
        return FlowValidationError(message)
