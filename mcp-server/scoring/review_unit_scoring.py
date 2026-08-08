"""Defines typed scoring of immutable reviewed units."""

from typing import Protocol

from findings.review_unit import ReviewUnit
from scoring.review_unit_scoring_result import ReviewUnitScoringResult


"""
solid-name: ReviewUnitScoring
solid-category: abstraction
solid-description: Contract for applying server-authoritative principle rules to one immutable reviewed code unit.
"""
class ReviewUnitScoring(Protocol):
    def score(self, unit: ReviewUnit, file_path: str) -> ReviewUnitScoringResult: ...
