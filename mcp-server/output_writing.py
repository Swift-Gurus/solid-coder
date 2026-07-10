"""
solid-description: Contract for writing payload data.
solid-category: abstraction
"""

from typing import Protocol


class OutputWriting(Protocol):
    """Protocol for writing a serialised hook payload to an output stream."""

    def write_payload(self, payload: dict) -> None: ...
