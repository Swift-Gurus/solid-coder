"""Defines ordered collection of unique strings."""

from typing import Protocol


"""
solid-name: OrderedStringCollecting
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for combining string collections while preserving first-seen order.
"""
class OrderedStringCollecting(Protocol):

    def collect(self, collections: list[list[str]]) -> list[str]: ...
