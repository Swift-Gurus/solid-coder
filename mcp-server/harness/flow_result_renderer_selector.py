"""
solid-name: FlowResultRendererSelector
solid-category: service
solid-spec: [SPEC-031]
solid-description: Routes flow result rendering based on feature configuration.
"""

from __future__ import annotations

from harness.flow_result_renderer_selecting import FlowResultRendererSelecting
from harness.flow_result_rendering import FlowResultRendering


class FlowResultRendererSelector(FlowResultRendererSelecting):

    def __init__(self, plain_text_renderer: FlowResultRendering, json_renderer: FlowResultRendering) -> None:
        self._plain_text_renderer = plain_text_renderer
        self._json_renderer = json_renderer

    def select(self, flow_plain_text_response: bool) -> FlowResultRendering:
        return self._plain_text_renderer if flow_plain_text_response else self._json_renderer
