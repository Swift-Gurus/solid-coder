"""Defines the immutable outcome of scoring one principle submission."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from findings.partial_review_output import PartialReviewOutput


"""
solid-name: PrincipleScoringResult
solid-category: model
solid-description: Carries either a scored immutable review output or the scoring failure that prevented it.
"""
@dataclass(frozen=True)
class PrincipleScoringResult:
    output: Optional[PartialReviewOutput] = None
    error_message: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        return self.output is not None and self.error_message is None
