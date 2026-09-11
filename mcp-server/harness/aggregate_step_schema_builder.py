"""Builds the response schema for one authored aggregate step."""

from harness.aggregate_step_schema_building import AggregateStepSchemaBuilding
from harness.authored_step_coordinate import AuthoredStepCoordinate
from harness.output_spec_schema_serializing import OutputSpecSchemaSerializing
from harness.strict_object_schema import StrictObjectSchema
from harness.strict_object_schema_building import StrictObjectSchemaBuilding


"""
solid-name: AggregateStepSchemaBuilder
solid-category: service
solid-spec: [SPEC-045]
solid-description: Builds a strict named-output schema for one authored aggregate step.
"""
class AggregateStepSchemaBuilder(AggregateStepSchemaBuilding):
    def __init__(
        self,
        output_serializer: OutputSpecSchemaSerializing,
        object_schema_builder: StrictObjectSchemaBuilding,
    ) -> None:
        self._output_serializer = output_serializer
        self._object_schema_builder = object_schema_builder

    def build(self, step: AuthoredStepCoordinate) -> StrictObjectSchema:
        return self._object_schema_builder.build(
            properties={
                output.name: self._output_serializer.serialize(output)
                for output in step.outputs
            },
            required=[output.name for output in step.outputs],
        )
