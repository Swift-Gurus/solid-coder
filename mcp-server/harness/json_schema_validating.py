"""
solid-description: Validates values against JSON Schema specifications.
solid-category: service
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

_MCP_DIR = Path(__file__).resolve().parents[1]
if str(_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_DIR))

from harness.models import ValidationResult

"""
solid-name: JsonSchemaValidating
solid-category: abstraction
solid-description: Contract for reporting whether data satisfies a JSON schema.
"""


class JsonSchemaValidating(Protocol):
    """
    solid-description: Contract for validating values against JSON Schema specifications.
    solid-category: abstraction
    """

    def validate(self, schema: dict, value: Any) -> ValidationResult: ...


"""
solid-name: JsonSchemaValidator
solid-category: service
solid-description: Validates JSON data and reports validation errors through structured results.
"""


class JsonSchemaValidator:
    """
    solid-description: Validates values against JSON Schema specifications.
    solid-category: service
    """

    def __init__(self, format_errors: Callable[[dict, Any], list[str]]) -> None:
        self._format_errors = format_errors

    def validate(self, schema: dict, value: Any) -> ValidationResult:
        try:
            errors = self._format_errors(schema, value)
            return ValidationResult(ok=not errors, errors=errors)
        except ImportError:
            return ValidationResult(
                ok=False, errors=["jsonschema package not installed"]
            )
        except Exception as exc:  # noqa: BLE001 — Formatter failures become explicit invalid ValidationResult values, never successful validation.
            return ValidationResult(ok=False, errors=[str(exc)])
