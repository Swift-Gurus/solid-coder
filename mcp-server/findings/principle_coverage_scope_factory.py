"""Constructs immutable principle coverage scopes."""

from collections.abc import Iterable

from findings.principle_coverage_scope import PrincipleCoverageScope
from findings.principle_coverage_scope_creating import PrincipleCoverageScopeCreating
from findings.review_unit_kind import ReviewUnitKind


"""
solid-name: PrincipleCoverageScopeFactory
solid-category: factory
solid-description: Constructs one immutable principle scope from validated labels and source-unit kinds.
"""
class PrincipleCoverageScopeFactory(PrincipleCoverageScopeCreating):
    def create(
        self,
        principle_label: str,
        unit_kinds: Iterable[ReviewUnitKind],
    ) -> PrincipleCoverageScope:
        return PrincipleCoverageScope(
            principle_label=principle_label,
            unit_kinds=frozenset(unit_kinds),
        )
