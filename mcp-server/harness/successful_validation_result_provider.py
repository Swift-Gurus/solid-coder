"""Supplies successful workflow validation results."""

from harness.validation_result import ValidationResult


"""
solid-name: SuccessfulValidationResultProvider
solid-category: factory
solid-spec: [SPEC-035]
solid-description: Supplies successful workflow validation results for accepted submissions.
"""
class SuccessfulValidationResultProvider:
    def provide(self) -> ValidationResult:
        return ValidationResult(ok=True)
