"""Defines workflow collection membership matching."""

from typing import Protocol


"""
solid-name: CollectionValueMatching
solid-category: abstraction
solid-spec: [SPEC-037, SPEC-039]
solid-description: Contract for finding a type-strict value within a workflow collection.
"""
class CollectionValueMatching(Protocol):
    def contains(self, collection: object, value: object) -> bool: ...
