"""
solid-name: StdoutSink
solid-category: abstraction
solid-description: Contract that defines buffered byte writing.
"""

from typing import Protocol


class StdoutSink(Protocol):
    def write(self, data: bytes) -> None: ...

    def flush(self) -> None: ...
