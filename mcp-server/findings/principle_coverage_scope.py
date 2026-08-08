"""Defines the source-unit kinds governed by one review principle."""

from dataclasses import dataclass

from findings.review_unit_kind import ReviewUnitKind


"""
solid-name: PrincipleCoverageScope
solid-category: model
solid-description: Associates one principle with the immutable source-unit kinds it is required to review.
"""
@dataclass(frozen=True)
class PrincipleCoverageScope:
    principle_label: str
    unit_kinds: frozenset[ReviewUnitKind]
