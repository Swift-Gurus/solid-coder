"""Composes Swift member inventory decoding."""

from harness.pydantic_model_decoder import PydanticModelDecoder
from source.members.source_member_kind import SourceMemberKind
from source.members.source_member_kind_registration import SourceMemberKindRegistration
from source.members.swift_declared_access_resolver import SwiftDeclaredAccessResolver
from source.members.swift_member_declaration import SwiftMemberDeclaration
from source.members.swift_member_decoder import SwiftMemberDecoder
from source.members.swift_member_visibility_resolver import SwiftMemberVisibilityResolver
from source.source_evidence_resolving import SourceEvidenceResolving


"""
solid-name: SwiftMemberDecoderFactory
solid-category: factory
solid-spec: [SPEC-062]
solid-description: Composes direct-member decoding with supported declaration kinds, access policy, and shared source evidence.
"""
class SwiftMemberDecoderFactory:
    def make(self, evidence: SourceEvidenceResolving) -> SwiftMemberDecoder:
        return SwiftMemberDecoder(
            model_decoder=PydanticModelDecoder(SwiftMemberDeclaration),
            visibility=SwiftMemberVisibilityResolver(SwiftDeclaredAccessResolver()),
            evidence=evidence,
            registrations=[
                SourceMemberKindRegistration("func_decl", SourceMemberKind.METHOD),
                SourceMemberKindRegistration("var_decl", SourceMemberKind.PROPERTY),
                SourceMemberKindRegistration("associated_type_decl", SourceMemberKind.ASSOCIATED_TYPE),
                SourceMemberKindRegistration("constructor_decl", SourceMemberKind.INITIALIZER),
                SourceMemberKindRegistration("destructor_decl", SourceMemberKind.DEINITIALIZER),
                SourceMemberKindRegistration("subscript_decl", SourceMemberKind.SUBSCRIPT),
            ],
        )
