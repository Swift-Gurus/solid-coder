"""Defines one immutable source-code unit in a review submission."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from findings.principle_metrics import PrincipleMetrics
from findings.review_unit_kind import ReviewUnitKind
from findings.review_violation import ReviewViolation


"""
solid-name: ReviewUnit
solid-category: model
solid-description: Represents one reviewed source-code unit and its principle measurements.
"""
@dataclass(frozen=True)
class ReviewUnit:
    name: str
    kind: ReviewUnitKind
    metrics: tuple[PrincipleMetrics, ...]
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    violations: tuple[ReviewViolation, ...] = field(default_factory=tuple)
