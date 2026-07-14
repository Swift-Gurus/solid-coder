"""
solid-description: Provides uniform content extraction from different tool inputs.
solid-category: service
solid-tags: [hook]
"""

from typing import Optional

_FIELD_BY_TOOL = {"Write": "content", "Edit": "new_string"}


class ToolContentExtractor:
    """Single source of truth for which tool_input field holds file content, per tool."""

    def content_for(self, tool_name: str, tool_input: dict) -> Optional[str]:
        field = _FIELD_BY_TOOL.get(tool_name)
        return tool_input.get(field, "") if field else None

    def input_key_for(self, tool_name: str) -> Optional[str]:
        return _FIELD_BY_TOOL.get(tool_name)
