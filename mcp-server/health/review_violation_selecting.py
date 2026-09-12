"""Defines severe review-violation selection."""

from typing import Protocol

from harness.review_result import ReviewResult
from health_violation import HealthViolation


"""
solid-name: ReviewViolationSelecting
solid-category: abstraction
solid-spec: [SPEC-036, SPEC-039]
solid-description: Contract for selecting blocking health violations from one scored review result.
"""
class ReviewViolationSelecting(Protocol):
    def select(self, result: ReviewResult) -> list[HealthViolation]: ...
