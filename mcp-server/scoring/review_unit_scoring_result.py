"""Defines the immutable outcome of scoring one reviewed code unit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from findings.review_unit import ReviewUnit


"""
solid-name: ReviewUnitScoringResult
solid-category: model
solid-description: Represents a unit-scoring outcome with either server-authoritative findings or failure information.
"""
@dataclass(frozen=True)
class ReviewUnitScoringResult:
    unit: Optional[ReviewUnit] = None
    error_message: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        return self.unit is not None and self.error_message is None
