"""
solid-name: HandlerStoring
solid-category: abstraction
solid-description: Contract for storing and looking up handler callables by name.
"""

from typing import Callable, Optional, Protocol


class HandlerStoring(Protocol):
    def add_handler(self, name: str, handler: Callable) -> None: ...

    def get(self, name: str) -> Optional[Callable]: ...
