"""Defines construction of configured pipeline tool callables."""

from typing import Protocol

from pipeline.tool_callables_building import ToolCallablesBuilding


"""
solid-name: PipelineToolCallablesCreating
solid-category: abstraction
solid-description: Contract for creating configured pipeline tool callables.
"""
class PipelineToolCallablesCreating(Protocol):
    def make_tool_callables(self) -> ToolCallablesBuilding: ...
