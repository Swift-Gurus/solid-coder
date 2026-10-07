"""Decodes direct Swift declaration members into generic source facts."""

from typing import Protocol

from tree_sitter import Node

from findings.review_unit_kind import ReviewUnitKind
from source.analysis.signatures.swift_member_syntax import SwiftMemberSyntax
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.members.source_member import SourceMember, SourceMemberSignature
from source.members.source_member_kind_registration import SourceMemberKindRegistration
from source.members.source_member_visibility import SourceMemberVisibility
from source.members.swift_member_visibility_resolver import SwiftMemberVisibilityResolving
from source.source_line_range import SourceLineRange


"""
solid-name: SwiftMembersDecoding
solid-category: abstraction
solid-spec: [SPEC-062]
solid-description: Contract for decoding a source unit's directly declared members.
"""
class SwiftMembersDecoding(Protocol):
    def decode(
        self, item: Node, owner_kind: ReviewUnitKind, owner_identity: str,
    ) -> list[SourceMember]: ...


"""
solid-name: SwiftMemberDecoder
solid-category: boundary-adapter
solid-spec: [SPEC-062, SPEC-057]
solid-description: Converts direct declaration members into ordered source facts with distinct identities, access, typed signatures, and line evidence.
"""
class SwiftMemberDecoder(SwiftMembersDecoding):
    def __init__(
        self,
        names: SourceSyntaxParsing[Node, list[Node]],
        access: SourceSyntaxParsing[Node, SourceMemberVisibility | None],
        spans: SourceSyntaxParsing[Node, SourceLineRange],
        visibility: SwiftMemberVisibilityResolving,
        registrations: list[SourceMemberKindRegistration],
        signatures: SourceSyntaxParsing[SwiftMemberSyntax, SourceMemberSignature],
    ) -> None:
        self._names = names
        self._access = access
        self._spans = spans
        self._visibility = visibility
        self._registrations = registrations
        self._signatures = signatures

    def decode(
        self, item: Node, owner_kind: ReviewUnitKind, owner_identity: str,
    ) -> list[SourceMember]:
        body = item.child_by_field_name("body")
        if body is None or owner_kind is ReviewUnitKind.FUNCTION:
            return []
        owner_access = self._access.parse(item) or SourceMemberVisibility.INTERNAL
        members: list[SourceMember] = []
        for declaration in body.named_children:
            registration = next(
                (entry for entry in self._registrations if entry.parser_kind == declaration.type),
                None,
            )
            if registration is None:
                continue
            access = self._visibility.resolve(
                owner_kind, owner_access, self._access.parse(declaration),
            )
            span = self._spans.parse(declaration)
            for name in self._names.parse(declaration):
                members.append(SourceMember(
                    identity=f"{owner_identity}/member:{name.start_byte}",
                    name=name.text.decode("utf-8"),
                    kind=registration.member_kind,
                    visibility=access,
                    span=span,
                    signature=self._signatures.parse(SwiftMemberSyntax(
                        declaration=declaration, name=name, kind=registration.member_kind,
                    )),
                ))
        return members
