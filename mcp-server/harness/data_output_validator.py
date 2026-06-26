"""
solid-description: Validates step output values against their schemas.
solid-category: service
"""

from __future__ import annotations

from typing import Any

from harness.json_schema_validating import JsonSchemaValidating
from harness.models import OutputSpec, ValidationResult
from harness.schema_resolving import SchemaResolving


class DataOutputValidator:
    """
    solid-description: Validates output values against their schemas.
    solid-category: service
    """

    def __init__(self, schema_resolver: SchemaResolving, json_schema: JsonSchemaValidating) -> None:
        self._resolver = schema_resolver
        self._json_schema = json_schema

    def validate(self, output_spec: OutputSpec, value: Any) -> ValidationResult:
        schema = self._resolver.resolve(output_spec)
        if schema is None:
            return ValidationResult(ok=True)
        return self._json_schema.validate(schema, value)
