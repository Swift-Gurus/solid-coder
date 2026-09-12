"""Defines persisted review-result loading."""

from typing import Protocol

from harness.review_result import ReviewResult


"""
solid-name: ReviewResultReading
solid-category: abstraction
solid-spec: [SPEC-036, SPEC-039]
solid-description: Contract for loading the authoritative scored review result of one flow run.
"""
class ReviewResultReading(Protocol):
    def read(self, run_id: str) -> ReviewResult: ...
