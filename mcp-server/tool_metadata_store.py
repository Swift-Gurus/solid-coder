"""
solid-name: ToolMetadataStore
solid-category: service
solid-description: Stores and provides access to tool metadata.
"""

from typing import Dict, Optional

from tool_metadata_storing import ToolMetadataStoring


class ToolMetadataStore(ToolMetadataStoring):

    def __init__(self) -> None:
        self._tools: Dict[str, dict] = {}

    def add_metadata(self, name: str, description: str, input_schema: dict, meta: Optional[dict] = None) -> None:
        entry: dict = {"name": name, "description": description, "inputSchema": input_schema}
        if meta is not None:
            entry["_meta"] = meta
        self._tools[name] = entry

    def list_all(self) -> list:
        return list(self._tools.values())
