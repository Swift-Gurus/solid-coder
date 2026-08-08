"""Defines the immutable result of scoring one rule against one code unit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from findings.review_severity import ReviewSeverity


"""
solid-name: UnitScoringResult
solid-category: model
solid-description: Represents the severity or validation failure produced when scoring one rule against one code unit.
"""
@dataclass(frozen=True)
class UnitScoringResult:
    metric_id: str
    severity: ReviewSeverity
    error_message: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        return self.error_message is None
