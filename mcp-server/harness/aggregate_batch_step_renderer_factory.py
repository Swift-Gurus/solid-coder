"""Assembles aggregate batch rendering."""

from harness.aggregate_assignment_collector import AggregateAssignmentCollector
from harness.aggregate_batch_step_renderer import AggregateBatchStepRenderer
from harness.aggregate_item_schema_builder import AggregateItemSchemaBuilder
from harness.aggregate_prompt_renderer import AggregatePromptRenderer
from harness.aggregate_response_schema_builder import AggregateResponseSchemaBuilder
from harness.aggregate_step_schema_builder import AggregateStepSchemaBuilder
from harness.aggregate_turn_compiler import AggregateTurnCompiler
from harness.aggregate_workflow_schema_builder import AggregateWorkflowSchemaBuilder
from harness.output_spec_schema_serializer import OutputSpecSchemaSerializer
from harness.strict_object_schema_builder import StrictObjectSchemaBuilder
from json_serializer import JsonSerializer


"""
solid-name: AggregateBatchStepRendererFactory
solid-category: factory
solid-spec: [SPEC-045]
solid-description: Assembles aggregate assignment rendering and strict response-schema construction.
"""
class AggregateBatchStepRendererFactory:
    def make(self) -> AggregateBatchStepRenderer:
        object_schema_builder = StrictObjectSchemaBuilder()
        return AggregateBatchStepRenderer(
            assignments=AggregateAssignmentCollector(),
            compiler=AggregateTurnCompiler(
                prompt_renderer=AggregatePromptRenderer(),
                schema_builder=AggregateResponseSchemaBuilder(
                    item_schema_builder=AggregateItemSchemaBuilder(
                        workflow_schema_builder=AggregateWorkflowSchemaBuilder(
                            step_schema_builder=AggregateStepSchemaBuilder(
                                output_serializer=OutputSpecSchemaSerializer(),
                                object_schema_builder=object_schema_builder,
                            ),
                            object_schema_builder=object_schema_builder,
                        ),
                        object_schema_builder=object_schema_builder,
                    ),
                    object_schema_builder=object_schema_builder,
                ),
            ),
            json_serializer=JsonSerializer(),
        )
