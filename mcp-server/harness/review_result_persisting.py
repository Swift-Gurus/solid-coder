"""Defines persistence of one aggregate review result."""

from pathlib import Path
from typing import Protocol

from harness.review_result import ReviewResult


"""
solid-name: ReviewResultPersisting
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for durably publishing the ordered aggregate result of a review workflow run.
"""
class ReviewResultPersisting(Protocol):
    def persist(
        self,
        run_directory: Path,
        result: ReviewResult,
    ) -> None: ...
