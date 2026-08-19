"""Defines Swift parser declaration-kind normalization."""

from typing import Optional, Protocol

from findings.review_unit_kind import ReviewUnitKind


"""
solid-name: SwiftASTUnitKindResolving
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for resolving external Swift declaration identity into the shared unit-kind vocabulary.
"""
class SwiftASTUnitKindResolving(Protocol):
    def resolve(
        self,
        raw_kind: object,
        actor_marker: object,
    ) -> Optional[ReviewUnitKind]: ...
