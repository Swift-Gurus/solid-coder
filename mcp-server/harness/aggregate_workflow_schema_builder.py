"""Builds the response schema for one aggregate workflow assignment."""

from harness.aggregate_assignment import AggregateAssignment
from harness.aggregate_step_schema_building import AggregateStepSchemaBuilding
from harness.aggregate_workflow_schema_building import AggregateWorkflowSchemaBuilding
from harness.strict_object_schema import StrictObjectSchema
from harness.strict_object_schema_building import StrictObjectSchemaBuilding


"""
solid-name: AggregateWorkflowSchemaBuilder
solid-category: service
solid-spec: [SPEC-045]
solid-description: Builds a strict step-addressed schema for one aggregate workflow assignment.
"""
class AggregateWorkflowSchemaBuilder(AggregateWorkflowSchemaBuilding):
    def __init__(
        self,
        step_schema_builder: AggregateStepSchemaBuilding,
        object_schema_builder: StrictObjectSchemaBuilding,
    ) -> None:
        self._step_schema_builder = step_schema_builder
        self._object_schema_builder = object_schema_builder

    def build(self, assignment: AggregateAssignment) -> StrictObjectSchema:
        return self._object_schema_builder.build(
            properties={
                step.step_id: self._step_schema_builder.build(step)
                for step in assignment.steps
            },
            required=[step.step_id for step in assignment.steps],
        )
