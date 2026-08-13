"""Defines successful workflow validation result provision."""

from typing import Protocol

from harness.validation_result import ValidationResult


"""
solid-name: SuccessfulValidationResultProviding
solid-category: abstraction
solid-spec: [SPEC-035]
solid-description: Contract for supplying a successful workflow validation result.
"""
class SuccessfulValidationResultProviding(Protocol):
    def provide(self) -> ValidationResult: ...
