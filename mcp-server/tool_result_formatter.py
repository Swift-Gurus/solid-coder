"""
solid-name: ToolResultFormatter
solid-category: service
solid-description: Shapes a tool handler's raw return value into the MCP tool-call response content.
"""

import json
from typing import Any

from tool_result_formatting import ToolResultFormatting

_DISPLAY_PREFIX = (
    "Show the following output to the user exactly as-is, "
    "without summarizing or paraphrasing, then proceed:\n\n"
)
_ERROR_MARKER = "**"


class ToolResultFormatter(ToolResultFormatting):

    def format(self, result: Any) -> dict:
        text = result if isinstance(result, str) else json.dumps(result, indent=2)
        is_error = isinstance(result, str) and result.startswith(_ERROR_MARKER)
        return {
            "content": [{"type": "text", "text": f"{_DISPLAY_PREFIX}{text}"}],
            "isError": is_error,
        }
