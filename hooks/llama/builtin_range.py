"""solid-description: Provides iteration up to a specified limit.
solid-category: utility
solid-tags: [hook, llm]
"""

from typing import Protocol


class RangeIterating(Protocol):
    def iterate(self, limit: int): ...


class BuiltinRange:
    """Boundary adapter: wraps the built-in range (stdlib, cannot be subclassed).

    range is a global built-in type — this adapter satisfies the
    OCP Boundary Adapter exception.
    """

    def iterate(self, limit: int):
        return range(limit)