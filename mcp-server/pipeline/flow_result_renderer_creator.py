"""Creates the configured production flow result renderer."""

from hc_config_schema import load_config
from harness.flow_result_json_renderer import FlowResultJsonRenderer
from harness.flow_result_rendering import FlowResultRendering
from harness.flow_result_renderer import FlowResultRenderer
from harness.flow_result_renderer_selector import FlowResultRendererSelector
from pipeline.flow_result_renderer_creating import FlowResultRendererCreating


"""
solid-name: FlowResultRendererCreator
solid-category: service
solid-description: Creates the configured production flow result renderer.
"""
class FlowResultRendererCreator(FlowResultRendererCreating):
    def create(self) -> FlowResultRendering:
        return FlowResultRendererSelector(
            plain_text_renderer=FlowResultRenderer(),
            json_renderer=FlowResultJsonRenderer(),
        ).select(load_config().feature_flags.flow_plain_text_response)
