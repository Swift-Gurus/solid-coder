"""Renders flow status snapshots for model-facing responses."""

from dataclasses import asdict

from harness.flow_status_rendering import FlowStatusRendering
from harness.flow_status_result import FlowStatusResult


"""
solid-name: FlowStatusResponseRenderer
solid-category: boundary-adapter
solid-spec: [SPEC-031]
solid-description: Renders flow status snapshots into structured model-facing responses.
"""
class FlowStatusResponseRenderer(FlowStatusRendering):
    def render(self, result: FlowStatusResult) -> dict:
        return asdict(result)
