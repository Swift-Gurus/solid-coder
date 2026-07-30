"""
solid-name: IncomingMessageReading
solid-category: abstraction
solid-description: Contract for reading the next incoming message.
"""

from typing import Optional, Protocol


class IncomingMessageReading(Protocol):
    def read_message(self) -> Optional[dict]: ...
