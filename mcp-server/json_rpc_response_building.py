"""
solid-name: JsonRpcResponseBuilding
solid-category: abstraction
solid-description: Contract for building JSON-RPC 2.0 success and error response envelopes.
"""

from typing import Any, Protocol


class JsonRpcResponseBuilding(Protocol):
    def success(self, id: Any, result: Any) -> dict: ...

    def error(self, id: Any, code: int, message: str) -> dict: ...
