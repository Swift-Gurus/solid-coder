"""
solid-name: ToolMetadataStoring
solid-category: abstraction
solid-description: Contract for storing and retrieving tool metadata.
"""

from typing import Optional, Protocol


class ToolMetadataStoring(Protocol):
    def add_metadata(self, name: str, description: str, input_schema: dict, meta: Optional[dict] = None) -> None: ...

    def list_all(self) -> list: ...
