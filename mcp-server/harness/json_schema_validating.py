"""
solid-description: Validates values against JSON Schema specifications.
solid-category: service
"""

from __future__ import annotations

from typing import Any, Protocol

from harness.models import ValidationResult


class JsonSchemaValidating(Protocol):
    """
    solid-description: Contract for validating values against JSON Schema specifications.
    solid-category: abstraction
    """

    def validate(self, schema: dict, value: Any) -> ValidationResult: ...


class JsonSchemaValidator:
    """
    solid-description: Validates values against JSON Schema specifications.
    solid-category: service
    """

    def validate(self, schema: dict, value: Any) -> ValidationResult:
        try:
            import jsonschema
            jsonschema.validate(instance=value, schema=schema)
            return ValidationResult(ok=True)
        except ImportError:
            return ValidationResult(ok=False, errors=["jsonschema package not installed"])
        except Exception as exc:
            return ValidationResult(ok=False, errors=[str(exc)])
