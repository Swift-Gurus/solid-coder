"""
solid-description: Contract for updating input data based on content changes.
solid-category: abstraction
solid-tags: [hook]
"""

from typing import Protocol


class ToolInputUpdating(Protocol):
    def build(self, tool_name: str, tool_input: dict, corrected: str, existing: str) -> dict: ...
