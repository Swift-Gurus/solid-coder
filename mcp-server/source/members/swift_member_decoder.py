"""Decodes direct Swift declaration members into generic source facts."""

from typing import Protocol

from harness.structured_model_decoding import StructuredModelDecoding
from source.members.source_member import SourceMember
from source.members.source_member_kind_registration import SourceMemberKindRegistration
from source.members.swift_member_declaration import SwiftMemberDeclaration
from source.members.swift_member_visibility_resolver import SwiftMemberVisibilityResolving
from source.source_evidence_resolving import SourceEvidenceResolving
from source.source_operation_error import SourceOperationError


"""
solid-name: SwiftMembersDecoding
solid-category: abstraction
solid-spec: [SPEC-062]
solid-description: Contract for decoding a source unit's directly declared members.
"""
class SwiftMembersDecoding(Protocol):
    def decode(self, item: object, owner_identity: str, source: str) -> list[SourceMember]: ...


"""
solid-name: SwiftMemberDecoder
solid-category: boundary-adapter
solid-spec: [SPEC-062]
solid-description: Converts direct declaration members into ordered source facts with distinct identities, access, and line evidence.
"""
class SwiftMemberDecoder(SwiftMembersDecoding):
    def __init__(
        self,
        model_decoder: StructuredModelDecoding[SwiftMemberDeclaration],
        visibility: SwiftMemberVisibilityResolving,
        evidence: SourceEvidenceResolving,
        registrations: list[SourceMemberKindRegistration],
    ) -> None:
        self._model_decoder = model_decoder
        self._visibility = visibility
        self._evidence = evidence
        self._registrations = registrations

    def decode(self, item: object, owner_identity: str, source: str) -> list[SourceMember]:
        owner = self._model_decoder.decode(item, "Swift member declaration")
        members: list[SourceMember] = []
        for declaration in owner.members:
            registration = next(
                (entry for entry in self._registrations if entry.parser_kind == declaration.kind),
                None,
            )
            if declaration.implicit or registration is None:
                continue
            if not declaration.name or declaration.start_offset is None or declaration.end_offset is None:
                raise SourceOperationError(
                    f"Missing name or source range for {declaration.kind} in {owner_identity}"
                )
            source_declaration = next(
                (
                    binding for binding in owner.members
                    if declaration.kind == "var_decl"
                    and binding.kind == "pattern_binding_decl"
                    and binding.start_offset is not None
                    and binding.end_offset is not None
                    and binding.start_offset <= declaration.start_offset <= binding.end_offset
                ),
                declaration,
            )
            members.append(SourceMember(
                identity=f"{owner_identity}/member:{declaration.start_offset}",
                name=declaration.name,
                kind=registration.member_kind,
                visibility=self._visibility.resolve(owner, declaration),
                span=self._evidence.resolve(
                    fact=declaration.name,
                    source=source,
                    start_offset=source_declaration.start_offset,
                    end_offset=source_declaration.end_offset,
                ).span,
            ))
        return members
