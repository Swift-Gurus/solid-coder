"""
solid-name: HandlerStoring
solid-category: abstraction
solid-description: Contract for storing and looking up handler callables by name.
"""

from collections.abc import Callable
from typing import Protocol


class HandlerStoring(Protocol):
    def add_handler(self, name: str, handler: Callable) -> None: ...

    def get(self, name: str) -> Callable | None: ...
