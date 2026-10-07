"""Composes Swift member inventory decoding."""

from source.analysis.swift_member_decoder import SwiftMemberDecoder
from source.analysis.tree_sitter_node_span_parser import TreeSitterNodeSpanParser
from source.analysis.tree_sitter_swift_access_parser import TreeSitterSwiftAccessParser
from source.analysis.tree_sitter_swift_binding_names_parser import TreeSitterSwiftBindingNamesParser
from source.analysis.tree_sitter_swift_member_names_parser import TreeSitterSwiftMemberNamesParser
from source.members.source_member_kind import SourceMemberKind
from source.members.source_member_kind_registration import SourceMemberKindRegistration
from source.members.swift_member_visibility_resolver import SwiftMemberVisibilityResolver


"""
solid-name: SwiftMemberDecoderFactory
solid-category: factory
solid-spec: [SPEC-062]
solid-description: Prepares a decoder for Swift source-member inventory analysis.
"""
class SwiftMemberDecoderFactory:
    def make(self) -> SwiftMemberDecoder:
        return SwiftMemberDecoder(
            names=TreeSitterSwiftMemberNamesParser(TreeSitterSwiftBindingNamesParser()),
            access=TreeSitterSwiftAccessParser(),
            spans=TreeSitterNodeSpanParser(),
            visibility=SwiftMemberVisibilityResolver(),
            registrations=[
                SourceMemberKindRegistration("function_declaration", SourceMemberKind.METHOD),
                SourceMemberKindRegistration("protocol_function_declaration", SourceMemberKind.METHOD),
                SourceMemberKindRegistration("property_declaration", SourceMemberKind.PROPERTY),
                SourceMemberKindRegistration("protocol_property_declaration", SourceMemberKind.PROPERTY),
                SourceMemberKindRegistration("associatedtype_declaration", SourceMemberKind.ASSOCIATED_TYPE),
                SourceMemberKindRegistration("init_declaration", SourceMemberKind.INITIALIZER),
                SourceMemberKindRegistration("deinit_declaration", SourceMemberKind.DEINITIALIZER),
                SourceMemberKindRegistration("subscript_declaration", SourceMemberKind.SUBSCRIPT),
            ],
        )
