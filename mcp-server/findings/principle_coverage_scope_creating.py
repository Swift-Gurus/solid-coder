"""Defines construction of immutable principle coverage scopes."""

from collections.abc import Iterable
from typing import Protocol

from findings.principle_coverage_scope import PrincipleCoverageScope
from findings.review_unit_kind import ReviewUnitKind


"""
solid-name: PrincipleCoverageScopeCreating
solid-category: abstraction
solid-description: Contract for constructing one principle coverage scope from validated domain values.
"""
class PrincipleCoverageScopeCreating(Protocol):
    def create(
        self,
        principle_label: str,
        unit_kinds: Iterable[ReviewUnitKind],
    ) -> PrincipleCoverageScope: ...
