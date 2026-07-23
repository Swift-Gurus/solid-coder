"""
solid-name: FlowResultRendererSelecting
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for selecting a flow result renderer based on feature configuration.
"""

from __future__ import annotations

from typing import Protocol

from harness.flow_result_rendering import FlowResultRendering


class FlowResultRendererSelecting(Protocol):

    def select(self, flow_plain_text_response: bool) -> FlowResultRendering: ...