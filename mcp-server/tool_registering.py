"""
solid-name: ToolRegistering
solid-category: abstraction
solid-description: Contract for registering a tool's metadata and handler as one operation.
"""

from collections.abc import Callable
from typing import Protocol


class ToolRegistering(Protocol):
    def register(
        self,
        name: str,
        description: str,
        input_schema: dict,
        handler: Callable,
        meta: dict | None = None,
    ) -> None: ...
