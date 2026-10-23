"""Defines selection of one numeric value from metric projections."""

from typing import Protocol

"""
solid-name: CollectionMetricValueSelecting
solid-category: abstraction
solid-spec: [SPEC-054]
solid-description: Contract for selecting one numeric result from validated metric projections.
"""


class CollectionMetricValueSelecting(Protocol):
    def select(self, values: list[object]) -> int | float: ...
