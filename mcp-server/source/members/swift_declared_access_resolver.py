"""Reads declared visibility from typed Swift parser attributes."""

from typing import Optional, Protocol

from source.members.source_member_visibility import SourceMemberVisibility
from source.members.swift_member_declaration import SwiftMemberDeclaration


"""
solid-name: SwiftDeclaredAccessResolving
solid-category: abstraction
solid-spec: [SPEC-062]
solid-description: Contract for reading declaration-level access without substituting setter-only restrictions.
"""
class SwiftDeclaredAccessResolving(Protocol):
    def resolve(self, declaration: SwiftMemberDeclaration) -> Optional[SourceMemberVisibility]: ...


"""
solid-name: SwiftDeclaredAccessResolver
solid-category: boundary-adapter
solid-spec: [SPEC-062]
solid-description: Resolves explicitly declared access to source members while preserving unspecified visibility.
"""
class SwiftDeclaredAccessResolver(SwiftDeclaredAccessResolving):
    def resolve(self, declaration: SwiftMemberDeclaration) -> Optional[SourceMemberVisibility]:
        return next(
            (
                attribute.access_level
                for attribute in declaration.attributes
                if attribute.kind == "access_control_attr"
                and attribute.access_level is not None
            ),
            None,
        )
