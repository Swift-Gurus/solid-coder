"""Builds the response schema for one aggregate item."""

from harness.aggregate_assignment import AggregateAssignment
from harness.aggregate_item_schema_building import AggregateItemSchemaBuilding
from harness.aggregate_workflow_schema_building import AggregateWorkflowSchemaBuilding
from harness.strict_object_schema import StrictObjectSchema
from harness.strict_object_schema_building import StrictObjectSchemaBuilding


"""
solid-name: AggregateItemSchemaBuilder
solid-category: service
solid-spec: [SPEC-045]
solid-description: Builds a strict workflow-addressed schema for one aggregate item label.
"""
class AggregateItemSchemaBuilder(AggregateItemSchemaBuilding):
    def __init__(
        self,
        workflow_schema_builder: AggregateWorkflowSchemaBuilding,
        object_schema_builder: StrictObjectSchemaBuilding,
    ) -> None:
        self._workflow_schema_builder = workflow_schema_builder
        self._object_schema_builder = object_schema_builder

    def build(
        self,
        item_label: str,
        assignments: list[AggregateAssignment],
    ) -> StrictObjectSchema:
        applicable = [
            assignment
            for assignment in assignments
            if assignment.item_label == item_label
        ]
        return self._object_schema_builder.build(
            properties={
                assignment.workflow_alias: self._workflow_schema_builder.build(
                    assignment
                )
                for assignment in applicable
            },
            required=[assignment.workflow_alias for assignment in applicable],
        )
