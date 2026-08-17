"""Rejects repeated string identities."""

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.unique_string_validating import UniqueStringValidating


"""
solid-name: UniqueStringValidator
solid-category: service
solid-spec: [SPEC-027, SPEC-039]
solid-description: Validates string identity collections and reports the first repeated value as a workflow error.
"""
class UniqueStringValidator(UniqueStringValidating):

    def __init__(self, error_factory: FlowValidationErrorCreating) -> None:
        self._error_factory = error_factory

    def validate(self, values: list[str], identity_name: str) -> None:
        seen: set[str] = set()
        for value in values:
            if value in seen:
                raise self._error_factory.create(
                    f"Duplicate {identity_name}: '{value}'"
                )
            seen.add(value)
