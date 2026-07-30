"""
solid-name: ToolsCallHandler
solid-category: service
solid-description: Executes tool invocation requests and returns their results with error handling.
"""

import json
from typing import Optional

from call_meta_providing import CallMetaProviding
from handler_storing import HandlerStoring
from tool_result_formatting import ToolResultFormatting
from tools_call_handling import ToolsCallHandling


class ToolsCallHandler(ToolsCallHandling, CallMetaProviding):

    def __init__(self, handlers: HandlerStoring, result_formatter: ToolResultFormatting) -> None:
        self._handlers = handlers
        self._result_formatter = result_formatter
        self._current_call_meta: dict = {}

    def get_current_call_meta(self) -> dict:
        return self._current_call_meta

    def handle(self, name: str, arguments: dict, meta: Optional[dict]) -> dict:
        self._current_call_meta = meta or {}
        handler = self._handlers.get(name)
        if handler is None:
            raise LookupError(f"Unknown tool: {name}")
        try:
            result = handler(**arguments)
        except Exception as e:
            return {"content": [{"type": "text", "text": json.dumps({"error": str(e)})}], "isError": True}
        return self._result_formatter.format(result)