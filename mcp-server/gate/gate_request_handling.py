"""Defines handling of one parsed pre-write gate request."""

from typing import Protocol


"""
solid-name: GateRequestHandling
solid-category: abstraction
solid-description: Contract for processing one parsed pre-write request through its applicable gate workflow.
solid-tags: [hook]
"""
class GateRequestHandling(Protocol):
    def handle(self, parsed: tuple) -> None: ...
