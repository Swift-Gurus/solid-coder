"""Defines persistence of a finalized rule review result."""

from pathlib import Path
from typing import Protocol

from harness.rule_review_result import RuleReviewResult


"""
solid-name: RuleReviewResultPersisting
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for durably publishing a finalized rule review result.
"""
class RuleReviewResultPersisting(Protocol):
    def persist(
        self,
        run_directory: Path,
        result: RuleReviewResult,
    ) -> None: ...
