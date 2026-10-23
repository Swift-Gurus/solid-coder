"""solid-name: ToolsCallHandling
solid-category: abstraction
solid-description: Contract for handling tool call execution with arguments and metadata.
"""

from typing import Protocol


class ToolsCallHandling(Protocol):
    def handle(self, name: str, arguments: dict, meta: dict | None) -> dict: ...
