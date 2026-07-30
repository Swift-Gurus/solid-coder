"""solid-name: MessageReading
solid-category: abstraction
solid-description: Contract for reading one framed message from a byte source.
"""

from typing import Optional, Protocol

from stdin_source import StdinSource


class MessageReading(Protocol):
    def read(self, stdin: StdinSource, peeked: bytes) -> Optional[dict]: ...