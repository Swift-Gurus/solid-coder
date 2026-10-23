"""
solid-name: ToolMetadataStoring
solid-category: abstraction
solid-description: Contract for storing and retrieving tool metadata.
"""

from typing import Protocol


class ToolMetadataStoring(Protocol):
    def add_metadata(
        self, name: str, description: str, input_schema: dict, meta: dict | None = None
    ) -> None: ...

    def list_all(self) -> list: ...
