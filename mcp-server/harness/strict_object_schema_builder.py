"""Constructs strict JSON object-schema models."""

from harness.strict_object_schema import StrictObjectSchema
from harness.strict_object_schema_building import StrictObjectSchemaBuilding


"""
solid-name: StrictObjectSchemaBuilder
solid-category: service
solid-spec: [SPEC-045]
solid-description: Constructs a closed JSON object schema from named properties and requirements.
"""
class StrictObjectSchemaBuilder(StrictObjectSchemaBuilding):
    def build(
        self,
        properties: dict[str, object],
        required: list[str],
    ) -> StrictObjectSchema:
        return StrictObjectSchema(properties=properties, required=required)
