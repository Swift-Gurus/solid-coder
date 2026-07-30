"""
solid-name: NoArgRpcHandling
solid-category: abstraction
solid-description: Contract for handling an RPC method that accepts no per-call arguments.
"""

from typing import Protocol


class NoArgRpcHandling(Protocol):
    def handle(self) -> dict: ...
