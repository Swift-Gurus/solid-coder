"""Defines type-strict value comparison."""

from typing import Protocol


"""
solid-name: StrictValueComparing
solid-category: abstraction
solid-spec: [SPEC-037, SPEC-039]
solid-description: Contract for comparing two values without cross-type coercion.
"""
class StrictValueComparing(Protocol):
    def equal(self, actual: object, expected: object) -> bool: ...
