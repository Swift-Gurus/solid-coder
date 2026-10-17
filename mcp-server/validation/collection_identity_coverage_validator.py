"""Shared boundary validation for exactly-once identity accounting."""

from typing import Protocol

from harness.flow_validation_error_creating import FlowValidationErrorCreating


"""
solid-name: CollectionIdentityCoverageValidating
solid-category: abstraction
solid-description: Contract for validating exactly-once accounting of an expected identity collection.
"""
class CollectionIdentityCoverageValidating(Protocol):
    def validate(self, expected_ids: list[str], submitted_ids: list[str], identity_name: str) -> None: ...


"""
solid-name: CollectionIdentityCoverageValidator
solid-category: service
solid-spec: [SPEC-057]
solid-description: Validates that submitted identities cover an expected collection exactly once and provides replacement guidance.
"""
class CollectionIdentityCoverageValidator(CollectionIdentityCoverageValidating):
    def __init__(self, error_factory: FlowValidationErrorCreating) -> None:
        self._error_factory = error_factory

    def validate(self, expected_ids: list[str], submitted_ids: list[str], identity_name: str) -> None:
        missing = [value for value in expected_ids if value not in submitted_ids]
        duplicate = [
            value for index, value in enumerate(submitted_ids)
            if value in submitted_ids[:index]
            and value not in submitted_ids[index + 1:]
        ]
        unknown = [value for value in submitted_ids if value not in expected_ids]
        problems = []
        if missing:
            problems.append(f"missing {identity_name} IDs {missing}")
        if duplicate:
            problems.append(f"duplicate {identity_name} IDs {duplicate}")
        if unknown:
            problems.append(f"unknown {identity_name} IDs {unknown}")
        if problems:
            raise self._error_factory.create(
                "; ".join(problems)
                + ". Resubmit one complete replacement for this step, with exactly one "
                + f"entry per expected {identity_name} ID; do not send only the missing entries."
            )
