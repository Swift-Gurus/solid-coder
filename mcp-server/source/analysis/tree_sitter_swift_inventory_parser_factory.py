"""Composes the Swift inventory parser."""

import tree_sitter_swift
from tree_sitter import Language, Parser

from findings.review_unit_kind_parser import ReviewUnitKindParser
from source.analysis.calls.tree_sitter_swift_call_parser import TreeSitterSwiftCallParser
from source.analysis.declarations.tree_sitter_swift_scope_parser import TreeSitterSwiftScopeParser
from source.analysis.declarations.tree_sitter_swift_scoped_declaration_parser import TreeSitterSwiftScopedDeclarationParser
from source.analysis.source_syntax_collection_parser import SourceSyntaxCollectionParser
from source.analysis.swift_member_decoder_factory import SwiftMemberDecoderFactory
from source.analysis.swift_syntax_diagnostic_parser import SwiftSyntaxDiagnosticParser
from source.analysis.tree_sitter_node_span_parser import TreeSitterNodeSpanParser
from source.analysis.tree_sitter_nodes_parser import TreeSitterNodesParser
from source.analysis.tree_sitter_swift_imports_parser import TreeSitterSwiftImportsParser
from source.analysis.signatures.tree_sitter_swift_declaration_signature_parser import TreeSitterSwiftDeclarationSignatureParser
from source.analysis.signatures.tree_sitter_syntax_tokens_parser import TreeSitterSyntaxTokensParser
from source.analysis.signatures.tree_sitter_type_reference_parser import TreeSitterTypeReferenceParser
from source.analysis.tree_sitter_swift_inventory_parser import TreeSitterSwiftInventoryParser
from source.analysis.tree_sitter_swift_signals_parser import TreeSitterSwiftSignalsParser
from source.analysis.tree_sitter_swift_unit_parser import TreeSitterSwiftUnitParser
from source.analysis.tree_sitter_syntax_parser import TreeSitterSyntaxParser
from source.analysis.type_inspections.tree_sitter_swift_type_inspection_parser import TreeSitterSwiftTypeInspectionParser


"""
solid-name: TreeSitterSwiftInventoryParserFactory
solid-category: factory
solid-spec: [SPEC-057, SPEC-063]
solid-description: Prepares a parser for complete and prospective Swift source inventories.
"""
class TreeSitterSwiftInventoryParserFactory:
    def make(self) -> TreeSitterSwiftInventoryParser:
        spans = TreeSitterNodeSpanParser()
        tokens = TreeSitterSyntaxTokensParser()
        nodes = TreeSitterNodesParser(
            excluded_node_types=frozenset({"comment", "multiline_comment"}),
            excluded_fields=frozenset({"text"}),
        )
        units = TreeSitterSwiftUnitParser(
            unit_kinds=ReviewUnitKindParser(),
            spans=spans,
            members=SwiftMemberDecoderFactory().make(),
            signatures=TreeSitterSwiftDeclarationSignatureParser(
                tokens=tokens,
                references=TreeSitterTypeReferenceParser(tokens=tokens, spans=spans),
            ),
        )
        return TreeSitterSwiftInventoryParser(
            syntax=TreeSitterSyntaxParser(Parser(Language(tree_sitter_swift.language()))),
            declarations=SourceSyntaxCollectionParser(
                entries=nodes,
                parser=TreeSitterSwiftScopedDeclarationParser(
                    units=units, scopes=TreeSitterSwiftScopeParser(spans), tokens=tokens,
                ),
            ),
            imports=TreeSitterSwiftImportsParser(spans),
            signals=TreeSitterSwiftSignalsParser(spans=spans, nodes=nodes),
            inspections=SourceSyntaxCollectionParser(
                entries=nodes,
                parser=TreeSitterSwiftTypeInspectionParser(spans=spans, tokens=tokens),
            ),
            calls=SourceSyntaxCollectionParser(
                entries=nodes,
                parser=TreeSitterSwiftCallParser(spans=spans, tokens=tokens),
            ),
            diagnostics=SourceSyntaxCollectionParser(
                entries=TreeSitterNodesParser(
                    excluded_node_types=frozenset(),
                    excluded_fields=frozenset(),
                ),
                parser=SwiftSyntaxDiagnosticParser(),
            ),
        )
