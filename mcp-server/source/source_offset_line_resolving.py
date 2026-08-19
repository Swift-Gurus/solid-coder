"""Defines source byte-offset to line conversion."""

from typing import Protocol


"""
solid-name: SourceOffsetLineResolving
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for resolving a UTF-8 source byte offset to a one-based line.
"""
class SourceOffsetLineResolving(Protocol):
    def resolve(self, source: str, offset: int) -> int: ...
