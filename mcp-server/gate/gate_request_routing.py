"""Defines routing of parsed pre-write gate requests."""

from typing import Protocol


"""
solid-name: GateRequestRouting
solid-category: abstraction
solid-description: Contract for routing a parsed pre-write request to its applicable handler.
solid-tags: [hook]
"""
class GateRequestRouting(Protocol):
    def route(self, parsed: tuple) -> None: ...
