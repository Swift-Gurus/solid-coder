"""
solid-name: HandlerStore
solid-category: service
solid-description: Provides storage and retrieval of handlers.
"""

from typing import Callable, Dict, Optional

from handler_storing import HandlerStoring


class HandlerStore(HandlerStoring):

    def __init__(self) -> None:
        self._handlers: Dict[str, Callable] = {}

    def add_handler(self, name: str, handler: Callable) -> None:
        self._handlers[name] = handler

    def get(self, name: str) -> Optional[Callable]:
        return self._handlers.get(name)
