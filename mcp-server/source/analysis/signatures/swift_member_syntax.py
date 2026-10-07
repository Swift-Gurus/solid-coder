"""Carries one declared member's syntax within the parser boundary."""

from dataclasses import dataclass

from tree_sitter import Node

from source.members.source_member_kind import SourceMemberKind


"""
solid-name: SwiftMemberSyntax
solid-category: model
solid-spec: [SPEC-057]
solid-description: Identifies one member binding within its declaration so structural extraction cannot mix sibling property signatures.
"""
@dataclass(frozen=True)
class SwiftMemberSyntax:
    declaration: Node
    name: Node
    kind: SourceMemberKind
