"""Defines construction of model-facing callable maps."""

from typing import Protocol


"""
solid-name: ToolCallablesBuilding
solid-category: abstraction
solid-description: Contract for constructing callable maps used by model-facing tool registries.
"""
class ToolCallablesBuilding(Protocol):
    def build(self) -> dict: ...
