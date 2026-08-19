"""Defines Swift parser declaration-name normalization."""

from typing import Optional, Protocol

from findings.review_unit_kind import ReviewUnitKind


"""
solid-name: SwiftASTUnitNameResolving
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for resolving external Swift declaration names for typed source units.
"""
class SwiftASTUnitNameResolving(Protocol):
    def resolve(
        self,
        kind: Optional[ReviewUnitKind],
        raw_name: object,
        extended_type: object,
    ) -> Optional[str]: ...
