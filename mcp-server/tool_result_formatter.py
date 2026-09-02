from typing import Any

from json_serializer import JsonSerializer, JsonSerializing
from tool_result_formatting import ToolResultFormatting

_ERROR_MARKER = "**"


"""
solid-name: ToolResultFormatter
solid-category: service
solid-description: Shapes a tool handler's raw return value into the MCP tool-call response content.
"""
class ToolResultFormatter(ToolResultFormatting):

    def __init__(
        self,
        serializer: JsonSerializing = JsonSerializer(),
    ) -> None:
        self._serializer = serializer

    def format(self, result: Any) -> dict:
        text = (
            result
            if isinstance(result, str)
            else self._serializer.serialize(result, indent=2)
        )
        is_error = isinstance(result, str) and result.startswith(_ERROR_MARKER)
        return {
            "content": [{"type": "text", "text": text}],
            "isError": is_error,
        }
