"""Coordinates typed inventory from a single Swift parse."""

from tree_sitter import Node, Tree

from source.analysis.source_syntax_inventory import SourceSyntaxInventory
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.analysis.type_inspections.source_type_inspection import SourceTypeInspection
from source.source_evidence import SourceEvidence
from source.source_parse_diagnostic import SourceParseDiagnostic
from source.source_unit import SourceUnit


"""
solid-name: TreeSitterSwiftInventoryParser
solid-category: service
solid-spec: [SPEC-057, SPEC-063]
solid-description: Provides a consistent Swift inventory of declarations, imports, syntax signals, type inspections and recoverable diagnostics.
"""
class TreeSitterSwiftInventoryParser(SourceSyntaxParsing[str, SourceSyntaxInventory]):
    def __init__(
        self,
        syntax: SourceSyntaxParsing[str, Tree],
        units: SourceSyntaxParsing[Node, SourceUnit | None],
        imports: SourceSyntaxParsing[Node, list[SourceEvidence]],
        signals: SourceSyntaxParsing[Node, list[SourceEvidence]],
        inspections: SourceSyntaxParsing[Node, list[SourceTypeInspection]],
        diagnostics: SourceSyntaxParsing[Node, list[SourceParseDiagnostic]],
    ) -> None:
        self._syntax = syntax
        self._units = units
        self._imports = imports
        self._signals = signals
        self._inspections = inspections
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
            type_inspections=self._inspections.parse(root),
            diagnostics=self._diagnostics.parse(root),
        )
