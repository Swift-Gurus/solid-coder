"""
solid-description: Validates step outputs against output specifications.
solid-category: service
"""

from __future__ import annotations

from typing import Any

from harness.output_validating import OutputValidating
from harness.models import OutputSpec, ValidationResult


class SchemaValidator:
    """
    solid-description: Validates step outputs against output specifications.
    solid-category: service
    """

    def __init__(self, validators: dict[str, OutputValidating]) -> None:
        self._validators = validators

    def validate(self, output_spec: OutputSpec, value: Any) -> ValidationResult:
        validator = self._validators.get(output_spec.type)
        if validator is None:
            return ValidationResult(ok=False, errors=[f"Unknown output type: '{output_spec.type}'"])
        return validator.validate(output_spec, value)