"""Creates the configured production flow result renderer."""

from solid_coder_config_loader import SolidCoderConfigLoader
from harness.batch_step_renderer_factory import BatchStepRendererFactory
from harness.first_ready_step_selector import FirstReadyStepSelector
from harness.flow_result_json_renderer import FlowResultJsonRenderer
from harness.flow_result_rendering import FlowResultRendering
from harness.flow_result_renderer import FlowResultRenderer
from harness.flow_result_renderer_selector import FlowResultRendererSelector
from harness.single_step_renderer import SingleStepRenderer
from harness.sibling_batch_step_selector_factory import (
    SiblingBatchStepSelectorFactory,
)
from harness.step_formatter import StepFormatter
from harness.step_renderer import StepRenderer
from harness.subagent_delegator import SubagentDelegator
from harness.terminal_message_resolver import TerminalMessageResolver
from pipeline.flow_result_renderer_creating import FlowResultRendererCreating
from harness.aggregate_step_schema_builder import AggregateStepSchemaBuilder
from harness.output_spec_schema_serializer import OutputSpecSchemaSerializer
from harness.strict_object_schema_builder import StrictObjectSchemaBuilder
from harness.submissions.flat_submission_step_renderer import FlatSubmissionStepRenderer
from harness.submissions.submission_format_step_renderer import SubmissionFormatStepRenderer
from json_serializer import JsonSerializer


"""
solid-name: FlowResultRendererCreator
solid-category: service
solid-description: Creates the configured production flow result renderer.
"""
class FlowResultRendererCreator(FlowResultRendererCreating):
    def create(self) -> FlowResultRendering:
        plain_text_renderer = FlowResultRenderer(
                step_renderer=SubmissionFormatStepRenderer(
                    ready_selector=FirstReadyStepSelector(),
                    sibling_selector=SiblingBatchStepSelectorFactory().make(),
                    flat_renderer=FlatSubmissionStepRenderer(
                        schema_builder=AggregateStepSchemaBuilder(
                            output_serializer=OutputSpecSchemaSerializer(),
                            object_schema_builder=StrictObjectSchemaBuilder(),
                        ),
                        serializer=JsonSerializer(),
                    ),
                    nested_renderer=StepRenderer(
                        ready_step_selector=FirstReadyStepSelector(),
                        sibling_batch_selector=SiblingBatchStepSelectorFactory().make(),
                        single_step_renderer=SingleStepRenderer(
                            subagent_delegator=SubagentDelegator(),
                            step_formatter=StepFormatter(),
                        ),
                        batch_step_renderer=BatchStepRendererFactory().make(),
                    ),
                ),
                terminal_message_resolver=TerminalMessageResolver(),
            )
        return FlowResultRendererSelector(
            plain_text_renderer=plain_text_renderer,
            json_renderer=FlowResultJsonRenderer(flat_renderer=plain_text_renderer),
        ).select(SolidCoderConfigLoader().load().feature_flags.flow_plain_text_response)
