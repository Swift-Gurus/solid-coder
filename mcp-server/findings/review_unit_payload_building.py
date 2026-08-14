"""Defines persisted payload construction for review units."""

from typing import Protocol

from findings.review_unit import ReviewUnit


"""
solid-name: ReviewUnitPayloadBuilding
solid-category: abstraction
solid-description: Contract for constructing the persisted payload for one reviewed unit.
"""
class ReviewUnitPayloadBuilding(Protocol):
    def build(self, unit: ReviewUnit) -> dict: ...
