"""Carries one declared member's syntax within the parser boundary."""

from dataclasses import dataclass

from source.members.source_member_kind import SourceMemberKind
from tree_sitter import Node

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
