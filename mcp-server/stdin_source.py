"""
solid-name: StdinSource
solid-category: abstraction
solid-description: Contract for reading raw bytes from a stream in fixed-size chunks or by line.
"""

from typing import Protocol


class StdinSource(Protocol):
    def read(self, n: int) -> bytes: ...

    def readline(self) -> bytes: ...