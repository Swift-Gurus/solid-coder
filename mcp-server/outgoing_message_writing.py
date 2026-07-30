"""
solid-name: OutgoingMessageWriting
solid-category: abstraction
solid-description: Contract for writing a message.
"""

from typing import Protocol


class OutgoingMessageWriting(Protocol):
    def write_message(self, msg: dict) -> None: ...
