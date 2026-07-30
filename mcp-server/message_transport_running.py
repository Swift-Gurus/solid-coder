"""
solid-name: MessageTransportRunning
solid-category: abstraction
solid-description: Contract for executing message transport operations.
"""

from typing import Protocol


class MessageTransportRunning(Protocol):
    def run(self) -> None: ...
