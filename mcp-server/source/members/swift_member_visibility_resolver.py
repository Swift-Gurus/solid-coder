"""Resolves source-member visibility from declarations and lexical owners."""

from typing import Protocol

from findings.review_unit_kind import ReviewUnitKind
from source.members.source_member_visibility import SourceMemberVisibility

"""
solid-name: SwiftMemberVisibilityResolving
solid-category: abstraction
solid-spec: [SPEC-062]
solid-description: Contract for resolving member access within a declaring unit.
"""


class SwiftMemberVisibilityResolving(Protocol):
    def resolve(
        self,
        owner_kind: ReviewUnitKind,
        owner_access: SourceMemberVisibility,
        member_access: SourceMemberVisibility | None,
    ) -> SourceMemberVisibility: ...


"""
solid-name: SwiftMemberVisibilityResolver
solid-category: service
solid-spec: [SPEC-062]
solid-description: Resolves member access using owner restrictions, protocol requirements, and extension defaults.
"""


class SwiftMemberVisibilityResolver(SwiftMemberVisibilityResolving):
    def resolve(
        self,
        owner_kind: ReviewUnitKind,
        owner_access: SourceMemberVisibility,
        member_access: SourceMemberVisibility | None,
    ) -> SourceMemberVisibility:
        if owner_kind is ReviewUnitKind.PROTOCOL:
            return owner_access
        if owner_kind is ReviewUnitKind.EXTENSION:
            return member_access or owner_access
        ordering = list(SourceMemberVisibility)
        return min(
            member_access or SourceMemberVisibility.INTERNAL,
            owner_access,
            key=ordering.index,
        )
