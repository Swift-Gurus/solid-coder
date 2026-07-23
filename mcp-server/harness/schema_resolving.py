"""
solid-description: Resolves JSON Schemas from OutputSpecs.
solid-category: service
"""

from __future__ import annotations

from typing import Protocol

from harness.models import OutputSpec


class SchemaResolving(Protocol):
    """
    solid-description: Contract for resolving a JSON Schema from an OutputSpec.
    solid-category: abstraction
    """

    def resolve(self, output_spec: OutputSpec) -> dict | None: ...


class SchemaResolver:
    """
    solid-description: Resolves a JSON Schema from an OutputSpec.
    solid-category: service
    """

    def resolve(self, output_spec: OutputSpec) -> dict | None:
        return output_spec.schema
