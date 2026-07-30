"""
solid-name: MCPServerRegistering
solid-category: abstraction
solid-description: Contract for registering tools with name, description, schema, and metadata.
"""

from typing import Any, Optional, Protocol


class MCPServerRegistering(Protocol):
    def tool(self, name: str, description: str, input_schema: dict, meta: Optional[dict] = None) -> Any: ...
