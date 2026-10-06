"""Resolves source-member visibility from declarations and lexical owners."""

from typing import Protocol

from source.members.source_member_visibility import SourceMemberVisibility
from source.members.swift_declared_access_resolver import SwiftDeclaredAccessResolving
from source.members.swift_member_declaration import SwiftMemberDeclaration


"""
solid-name: SwiftMemberVisibilityResolving
solid-category: abstraction
solid-spec: [SPEC-062]
solid-description: Contract for resolving member access within a declaring unit.
"""
class SwiftMemberVisibilityResolving(Protocol):
    def resolve(
        self, owner: SwiftMemberDeclaration, member: SwiftMemberDeclaration,
    ) -> SourceMemberVisibility: ...


"""
solid-name: SwiftMemberVisibilityResolver
solid-category: service
solid-spec: [SPEC-062]
solid-description: Resolves member access using owner restrictions, protocol requirements, and extension defaults.
"""
class SwiftMemberVisibilityResolver(SwiftMemberVisibilityResolving):
    def __init__(self, declared_access: SwiftDeclaredAccessResolving) -> None:
        self._declared_access = declared_access

    def resolve(
        self, owner: SwiftMemberDeclaration, member: SwiftMemberDeclaration,
    ) -> SourceMemberVisibility:
        owner_access = self._declared_access.resolve(owner) or SourceMemberVisibility.INTERNAL
        if owner.kind == "protocol":
            return owner_access
        member_access = self._declared_access.resolve(member)
        if owner.kind == "extension_decl":
            return member_access or owner_access
        ordering = list(SourceMemberVisibility)
        return min(
            member_access or SourceMemberVisibility.INTERNAL,
            owner_access,
            key=ordering.index,
        )
