"""Coordinates typed inventory from a single Swift parse."""

from tree_sitter import Node, Tree

from source.analysis.source_syntax_inventory import SourceSyntaxInventory
from source.analysis.swift_parse_diagnostics_resolver import SwiftParseDiagnosticsResolving
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.source_evidence import SourceEvidence
from source.source_unit import SourceUnit


"""
solid-name: TreeSitterSwiftInventoryParser
solid-category: facade
solid-spec: [SPEC-057]
solid-description: Provides a consistent Swift inventory of source units, imports, syntax signals, and recoverable diagnostics.
"""
class TreeSitterSwiftInventoryParser(SourceSyntaxParsing[str, SourceSyntaxInventory]):
    def __init__(
        self,
        syntax: SourceSyntaxParsing[str, Tree],
        units: SourceSyntaxParsing[Node, SourceUnit | None],
        imports: SourceSyntaxParsing[Node, list[SourceEvidence]],
        signals: SourceSyntaxParsing[Node, list[SourceEvidence]],
        diagnostics: SwiftParseDiagnosticsResolving,
    ) -> None:
        self._syntax = syntax
        self._units = units
        self._imports = imports
        self._signals = signals
        self._diagnostics = diagnostics

    def parse(self, source: str) -> SourceSyntaxInventory:
        root = self._syntax.parse(source).root_node
        return SourceSyntaxInventory(
            units=[
                unit for child in root.named_children
                if (unit := self._units.parse(child)) is not None
            ],
            imports=self._imports.parse(root),
            signals=self._signals.parse(root),
            diagnostics=self._diagnostics.resolve(root),
        )
