"""Defines one immutable server-authoritative review violation."""

from __future__ import annotations

from dataclasses import dataclass

from findings.review_severity import ReviewSeverity


"""
solid-name: ReviewViolation
solid-category: model
solid-description: Represents one scored rule violation with its server-authoritative severity.
"""
@dataclass(frozen=True)
class ReviewViolation:
    rule_id: str
    severity: ReviewSeverity
