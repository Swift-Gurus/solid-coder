"""
solid-description: Contract for components that log a message.
solid-category: abstraction
"""

from typing import Protocol


class Logging(Protocol):
    def log(self, msg: str) -> None: ...
