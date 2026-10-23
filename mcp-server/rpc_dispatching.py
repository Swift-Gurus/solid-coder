"""
solid-name: RpcDispatching
solid-category: abstraction
solid-description: Contract for routing method calls to their handlers.
"""

from typing import Any, Protocol


class RpcDispatching(Protocol):
    def dispatch(self, method: str, id: Any, params: dict) -> dict | None: ...
