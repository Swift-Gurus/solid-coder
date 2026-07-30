"""
solid-name: ToolRegistering
solid-category: abstraction
solid-description: Contract for registering a tool's metadata and handler as one operation.
"""

from typing import Callable, Optional, Protocol


class ToolRegistering(Protocol):
    def register(
        self, name: str, description: str, input_schema: dict, handler: Callable, meta: Optional[dict] = None
    ) -> None: ...