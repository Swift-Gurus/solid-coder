"""
solid-description: Validates values against JSON Schema specifications.
solid-category: service
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Protocol

_MCP_DIR = Path(__file__).resolve().parents[1]
if str(_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_DIR))

from jsonschema_error_formatter import format_schema_errors  # noqa: E402

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
            errors = format_schema_errors(schema, value)
            return ValidationResult(ok=not errors, errors=errors)
        except ImportError:
            return ValidationResult(ok=False, errors=["jsonschema package not installed"])
        except Exception as exc:
            return ValidationResult(ok=False, errors=[str(exc)])