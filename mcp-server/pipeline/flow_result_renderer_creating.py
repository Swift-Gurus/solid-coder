"""Defines construction of the configured flow result renderer."""

from typing import Protocol

from harness.flow_result_rendering import FlowResultRendering


"""
solid-name: FlowResultRendererCreating
solid-category: abstraction
solid-description: Contract for creating the configured flow result renderer.
"""
class FlowResultRendererCreating(Protocol):
    def create(self) -> FlowResultRendering: ...
