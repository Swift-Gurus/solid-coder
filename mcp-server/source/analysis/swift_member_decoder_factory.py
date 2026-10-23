"""Composes Swift member inventory decoding."""

from source.analysis.signatures.tree_sitter_swift_accessors_parser import (
    TreeSitterSwiftAccessorsParser,
)
from source.analysis.signatures.tree_sitter_swift_associated_type_signature_parser import (
    TreeSitterSwiftAssociatedTypeSignatureParser,
)
from source.analysis.signatures.tree_sitter_swift_callable_signature_parser import (
    TreeSitterSwiftCallableSignatureParser,
)
from source.analysis.signatures.tree_sitter_swift_member_signature_parser import (
    TreeSitterSwiftMemberSignatureParser,
)
from source.analysis.signatures.tree_sitter_swift_parameters_parser import (
    TreeSitterSwiftParametersParser,
)
from source.analysis.signatures.tree_sitter_swift_subscript_signature_parser import (
    TreeSitterSwiftSubscriptSignatureParser,
)
from source.analysis.signatures.tree_sitter_swift_value_signature_parser import (
    TreeSitterSwiftValueSignatureParser,
)
from source.analysis.signatures.tree_sitter_syntax_tokens_parser import (
    TreeSitterSyntaxTokensParser,
)
from source.analysis.swift_member_decoder import SwiftMemberDecoder
from source.analysis.tree_sitter_node_span_parser import TreeSitterNodeSpanParser
from source.analysis.tree_sitter_swift_access_parser import TreeSitterSwiftAccessParser
from source.analysis.tree_sitter_swift_binding_names_parser import (
    TreeSitterSwiftBindingNamesParser,
)
from source.analysis.tree_sitter_swift_member_names_parser import (
    TreeSitterSwiftMemberNamesParser,
)
from source.members.source_member_kind import SourceMemberKind
from source.members.source_member_kind_registration import SourceMemberKindRegistration
from source.members.swift_member_visibility_resolver import (
    SwiftMemberVisibilityResolver,
)

"""
solid-name: SwiftMemberDecoderFactory
solid-category: factory
solid-spec: [SPEC-062, SPEC-057]
solid-description: Prepares a decoder for Swift source-member inventory and typed signature analysis.
"""


class SwiftMemberDecoderFactory:
    def make(self) -> SwiftMemberDecoder:
        tokens = TreeSitterSyntaxTokensParser()
        accessors = TreeSitterSwiftAccessorsParser(tokens)
        callables = TreeSitterSwiftCallableSignatureParser(
            tokens=tokens,
            parameters=TreeSitterSwiftParametersParser(tokens),
        )
        signatures = TreeSitterSwiftMemberSignatureParser(
            callables=callables,
            values=TreeSitterSwiftValueSignatureParser(tokens, accessors),
            associated_types=TreeSitterSwiftAssociatedTypeSignatureParser(tokens),
            subscripts=TreeSitterSwiftSubscriptSignatureParser(callables, accessors),
        )
        return SwiftMemberDecoder(
            names=TreeSitterSwiftMemberNamesParser(TreeSitterSwiftBindingNamesParser()),
            access=TreeSitterSwiftAccessParser(),
            spans=TreeSitterNodeSpanParser(),
            visibility=SwiftMemberVisibilityResolver(),
            signatures=signatures,
            registrations=[
                SourceMemberKindRegistration(
                    "function_declaration", SourceMemberKind.METHOD
                ),
                SourceMemberKindRegistration(
                    "protocol_function_declaration", SourceMemberKind.METHOD
                ),
                SourceMemberKindRegistration(
                    "property_declaration", SourceMemberKind.PROPERTY
                ),
                SourceMemberKindRegistration(
                    "protocol_property_declaration", SourceMemberKind.PROPERTY
                ),
                SourceMemberKindRegistration(
                    "associatedtype_declaration", SourceMemberKind.ASSOCIATED_TYPE
                ),
                SourceMemberKindRegistration(
                    "init_declaration", SourceMemberKind.INITIALIZER
                ),
                SourceMemberKindRegistration(
                    "deinit_declaration", SourceMemberKind.DEINITIALIZER
                ),
                SourceMemberKindRegistration(
                    "subscript_declaration", SourceMemberKind.SUBSCRIPT
                ),
            ],
        )
