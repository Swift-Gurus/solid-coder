"""
solid-name: ToolResultFormatting
solid-category: abstraction
solid-description: Contract for formatting any result as a dictionary.
"""

from typing import Any, Protocol


class ToolResultFormatting(Protocol):
    def format(self, result: Any) -> dict: ...
