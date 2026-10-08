"""Composes the Swift inventory parser."""

import tree_sitter_swift
from tree_sitter import Language, Parser

from findings.review_unit_kind_parser import ReviewUnitKindParser
from source.analysis.swift_member_decoder_factory import SwiftMemberDecoderFactory
from source.analysis.swift_parse_diagnostics_resolver import SwiftParseDiagnosticsResolver
from source.analysis.tree_sitter_node_span_parser import TreeSitterNodeSpanParser
from source.analysis.tree_sitter_swift_imports_parser import TreeSitterSwiftImportsParser
from source.analysis.signatures.tree_sitter_swift_declaration_signature_parser import TreeSitterSwiftDeclarationSignatureParser
from source.analysis.signatures.tree_sitter_syntax_tokens_parser import TreeSitterSyntaxTokensParser
from source.analysis.signatures.tree_sitter_type_reference_parser import TreeSitterTypeReferenceParser
from source.analysis.tree_sitter_swift_inventory_parser import TreeSitterSwiftInventoryParser
from source.analysis.tree_sitter_swift_signals_parser import TreeSitterSwiftSignalsParser
from source.analysis.tree_sitter_swift_unit_parser import TreeSitterSwiftUnitParser
from source.analysis.tree_sitter_syntax_parser import TreeSitterSyntaxParser


"""
solid-name: TreeSitterSwiftInventoryParserFactory
solid-category: factory
solid-spec: [SPEC-057]
solid-description: Prepares a parser for complete and prospective Swift source inventories.
"""
class TreeSitterSwiftInventoryParserFactory:
    def make(self) -> TreeSitterSwiftInventoryParser:
        spans = TreeSitterNodeSpanParser()
        tokens = TreeSitterSyntaxTokensParser()
        return TreeSitterSwiftInventoryParser(
            syntax=TreeSitterSyntaxParser(Parser(Language(tree_sitter_swift.language()))),
            units=TreeSitterSwiftUnitParser(
                unit_kinds=ReviewUnitKindParser(),
                spans=spans,
                members=SwiftMemberDecoderFactory().make(),
                signatures=TreeSitterSwiftDeclarationSignatureParser(
                    tokens=tokens,
                    references=TreeSitterTypeReferenceParser(tokens=tokens, spans=spans),
                ),
            ),
            imports=TreeSitterSwiftImportsParser(spans),
            signals=TreeSitterSwiftSignalsParser(spans),
            diagnostics=SwiftParseDiagnosticsResolver(),
        )
