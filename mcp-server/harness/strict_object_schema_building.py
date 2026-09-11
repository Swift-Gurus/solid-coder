"""Declares strict JSON object-schema construction."""

from typing import Protocol

from harness.strict_object_schema import StrictObjectSchema


"""
solid-name: StrictObjectSchemaBuilding
solid-category: abstraction
solid-spec: [SPEC-045]
solid-description: Contract for constructing a closed JSON object schema from named properties and requirements.
"""
class StrictObjectSchemaBuilding(Protocol):
    def build(
        self,
        properties: dict[str, object],
        required: list[str],
    ) -> StrictObjectSchema: ...
