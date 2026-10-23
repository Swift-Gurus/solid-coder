"""Coordinates typed inventory from a single Swift parse."""

from source.analysis.calls.source_call import SourceCall
from source.analysis.declarations.source_scoped_declaration import (
    SourceScopedDeclaration,
)
from source.analysis.source_syntax_inventory import SourceSyntaxInventory
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.analysis.type_inspections.source_type_inspection import SourceTypeInspection
from source.source_evidence import SourceEvidence
from source.source_parse_diagnostic import SourceParseDiagnostic
from tree_sitter import Node, Tree

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
        imports: SourceSyntaxParsing[Node, list[SourceEvidence]],
        signals: SourceSyntaxParsing[Node, list[SourceEvidence]],
        inspections: SourceSyntaxParsing[Node, list[SourceTypeInspection]],
        calls: SourceSyntaxParsing[Node, list[SourceCall]],
        diagnostics: SourceSyntaxParsing[Node, list[SourceParseDiagnostic]],
        declarations: SourceSyntaxParsing[Node, list[SourceScopedDeclaration]],
    ) -> None:
        self._syntax = syntax
        self._imports = imports
        self._signals = signals
        self._inspections = inspections
        self._calls = calls
        self._diagnostics = diagnostics
        self._declarations = declarations

    def parse(self, source: str) -> SourceSyntaxInventory:
        root = self._syntax.parse(source).root_node
        declarations = self._declarations.parse(root)
        top_level_offsets = {child.start_byte for child in root.named_children}
        return SourceSyntaxInventory(
            units=[
                entry.unit
                for entry in declarations
                if entry.unit.start_offset in top_level_offsets
            ],
            imports=self._imports.parse(root),
            declarations=declarations,
            signals=self._signals.parse(root),
            type_inspections=self._inspections.parse(root),
            calls=self._calls.parse(root),
            diagnostics=self._diagnostics.parse(root),
        )
