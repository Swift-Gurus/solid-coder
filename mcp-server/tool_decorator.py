"""
solid-name: ToolDecorator
solid-category: service
solid-description: Registers tool functions as MCP tools.
"""

from typing import Any, Callable, Optional

from mcp_server_registering import MCPServerRegistering
from tool_registering import ToolRegistering


class ToolDecorator(MCPServerRegistering):

    def __init__(self, registrar: ToolRegistering) -> None:
        self._registrar = registrar

    def tool(self, name: str, description: str, input_schema: dict, meta: Optional[dict] = None) -> Any:
        def decorator(fn: Callable) -> Callable:
            self._registrar.register(name, description, input_schema, fn, meta)
            return fn
        return decorator
