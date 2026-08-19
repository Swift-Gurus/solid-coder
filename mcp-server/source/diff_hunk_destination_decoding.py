"""Defines decoding of unified-diff destination positions."""

from typing import Protocol


"""
solid-name: DiffHunkDestinationDecoding
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for decoding a destination start line from a unified-diff hunk header.
"""
class DiffHunkDestinationDecoding(Protocol):
    def decode(self, header: str) -> int: ...
