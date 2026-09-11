"""Builds exact JSON Schema for aggregate workflow submissions."""

from harness.aggregate_assignment import AggregateAssignment
from harness.aggregate_item_schema_building import AggregateItemSchemaBuilding
from harness.aggregate_response_schema_building import AggregateResponseSchemaBuilding
from harness.strict_object_schema_building import StrictObjectSchemaBuilding


"""
solid-name: AggregateResponseSchemaBuilder
solid-category: service
solid-spec: [SPEC-045]
solid-description: Serializes typed item-level aggregate contracts into a strict model-response schema.
"""
class AggregateResponseSchemaBuilder(AggregateResponseSchemaBuilding):
    def __init__(
        self,
        item_schema_builder: AggregateItemSchemaBuilding,
        object_schema_builder: StrictObjectSchemaBuilding,
    ) -> None:
        self._item_schema_builder = item_schema_builder
        self._object_schema_builder = object_schema_builder

    def build(self, assignments: list[AggregateAssignment]) -> dict[str, object]:
        item_labels: list[str] = []
        for assignment in assignments:
            if assignment.item_label not in item_labels:
                item_labels.append(assignment.item_label)

        schema = self._object_schema_builder.build(
            properties={
                label: self._item_schema_builder.build(label, assignments)
                for label in item_labels
            },
            required=item_labels,
        )
        return schema.model_dump(by_alias=True)
