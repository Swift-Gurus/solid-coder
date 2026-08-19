"""Implements type-strict value comparison."""

from harness.strict_value_comparing import StrictValueComparing


"""
solid-name: StrictValueComparator
solid-category: service
solid-spec: [SPEC-037, SPEC-039]
solid-description: Compares two values only when their runtime classes and values are equal.
"""
class StrictValueComparator(StrictValueComparing):
    def equal(self, actual: object, expected: object) -> bool:
        return actual.__class__ is expected.__class__ and actual == expected
