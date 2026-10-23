"""
solid-name: HandlerStore
solid-category: service
solid-description: Provides storage and retrieval of handlers.
"""

from collections.abc import Callable

from handler_storing import HandlerStoring


class HandlerStore(HandlerStoring):
    def __init__(self) -> None:
        self._handlers: dict[str, Callable] = {}

    def add_handler(self, name: str, handler: Callable) -> None:
        self._handlers[name] = handler

    def get(self, name: str) -> Callable | None:
        return self._handlers.get(name)
