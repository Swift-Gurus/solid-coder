"""solid-description: Registers tool handlers with an MCP server by name, description, and schema.
solid-category: utility
solid-tags: [utility, service]
"""

from typing import Any, Callable, Optional

from common.mcp_meta import LARGE_OUTPUT
from mcp_server_registering import MCPServerRegistering  # noqa: F401 — re-exported for consumers
from tool_registering import ToolRegistering  # noqa: F401 — re-exported for consumers


class ToolRegistry:
    """Registers tool handlers with an MCPServer using the decorator protocol.

    Single responsibility: translate (name, description, schema, handler) tuples
    into registered MCP tools. No tool logic or service wiring.
    """

    def __init__(self, server: MCPServerRegistering) -> None:
        self._server = server

    def register(
        self,
        name: str,
        description: str,
        input_schema: dict,
        handler: Callable,
        meta: Optional[dict] = None,
    ) -> None:
        @self._server.tool(name=name, description=description,
                           input_schema=input_schema, meta=meta or LARGE_OUTPUT)
        def _wrapper(*args: Any, **kwargs: Any) -> Any:
            return handler(*args, **kwargs)