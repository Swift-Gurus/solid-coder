"""Defines model-facing rendering of flow status results."""

from typing import Protocol

from harness.flow_status_result import FlowStatusResult


"""
solid-name: FlowStatusRendering
solid-category: abstraction
solid-spec: [SPEC-031]
solid-description: Contract for rendering a flow status snapshot into a model-facing response.
"""
class FlowStatusRendering(Protocol):
    def render(self, result: FlowStatusResult) -> dict: ...
