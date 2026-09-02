"""Creates the configured production flow result renderer."""

from hc_config_schema import load_config
from harness.batch_step_item_renderer import BatchStepItemRenderer
from harness.batch_step_renderer import BatchStepRenderer
from harness.first_ready_step_selector import FirstReadyStepSelector
from harness.flow_result_json_renderer import FlowResultJsonRenderer
from harness.flow_result_rendering import FlowResultRendering
from harness.flow_result_renderer import FlowResultRenderer
from harness.flow_result_renderer_selector import FlowResultRendererSelector
from harness.single_step_renderer import SingleStepRenderer
from harness.sibling_batch_step_selector import SiblingBatchStepSelector
from harness.step_formatter import StepFormatter
from harness.step_renderer import StepRenderer
from harness.subagent_delegator import SubagentDelegator
from harness.terminal_message_resolver import TerminalMessageResolver
from pipeline.flow_result_renderer_creating import FlowResultRendererCreating


"""
solid-name: FlowResultRendererCreator
solid-category: service
solid-description: Creates the configured production flow result renderer.
"""
class FlowResultRendererCreator(FlowResultRendererCreating):
    def create(self) -> FlowResultRendering:
        return FlowResultRendererSelector(
            plain_text_renderer=FlowResultRenderer(
                step_renderer=StepRenderer(
                    ready_step_selector=FirstReadyStepSelector(),
                    sibling_batch_selector=SiblingBatchStepSelector(),
                    single_step_renderer=SingleStepRenderer(
                        subagent_delegator=SubagentDelegator(),
                        step_formatter=StepFormatter(),
                    ),
                    batch_step_renderer=BatchStepRenderer(
                        item_renderer=BatchStepItemRenderer()
                    ),
                ),
                terminal_message_resolver=TerminalMessageResolver(),
            ),
            json_renderer=FlowResultJsonRenderer(),
        ).select(load_config().feature_flags.flow_plain_text_response)
