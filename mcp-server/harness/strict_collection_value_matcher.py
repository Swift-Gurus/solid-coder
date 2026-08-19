"""Implements type-strict workflow collection membership."""

from harness.collection_value_matching import CollectionValueMatching
from harness.strict_value_comparing import StrictValueComparing


"""
solid-name: StrictCollectionValueMatcher
solid-category: service
solid-spec: [SPEC-037, SPEC-039]
solid-description: Finds a value in a list using injected type-strict equality semantics.
"""
class StrictCollectionValueMatcher(CollectionValueMatching):
    def __init__(self, comparator: StrictValueComparing) -> None:
        self._comparator = comparator

    def contains(self, collection: object, value: object) -> bool:
        if not isinstance(collection, list):
            return False
        return any(
            self._comparator.equal(value, candidate)
            for candidate in collection
        )
