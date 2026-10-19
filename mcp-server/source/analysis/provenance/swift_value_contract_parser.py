"""Resolves explicit types from semantically bound Swift value declarations."""

from pathlib import Path

from pydantic import FileUrl
from tree_sitter import Node

from source.analysis.provenance.semantic_position import SemanticPosition
from source.analysis.provenance.semantic_symbol_kind import SemanticSymbolKind
from source.analysis.provenance.source_symbol_provenance import SourceSymbolResolution
from source.analysis.provenance.source_unresolved_symbol import SourceUnresolvedSymbol
from source.analysis.provenance.sourcekit_document import SemanticSymbolLookingUp
from source.analysis.provenance.sourcekit_symbol import SourceKitSymbol
from source.analysis.provenance.utf16_source_position_resolver import SourceCoordinateResolving
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.repository_source_snapshot import RepositorySourceSnapshot


"""
solid-name: SwiftValueContractParser
solid-category: boundary-adapter
solid-spec: [SPEC-064]
solid-description: Resolves a value's explicit contract without substituting the value declaration for its type.
"""
class SwiftValueContractParser(SourceSyntaxParsing[list[SourceKitSymbol], SourceSymbolResolution]):
    def __init__(
        self,
        source: RepositorySourceSnapshot,
        annotations: SourceSyntaxParsing[int, Node | None],
        document: SemanticSymbolLookingUp,
        paths: SourceSyntaxParsing[FileUrl, Path | None],
        offsets: SourceCoordinateResolving[SemanticPosition, int],
        positions: SourceSyntaxParsing[Node, int | None],
        types: SourceSyntaxParsing[list[SourceKitSymbol], SourceSymbolResolution],
    ) -> None:
        self._source = source
        self._annotations = annotations
        self._document = document
        self._paths = paths
        self._offsets = offsets
        self._positions = positions
        self._types = types

    def parse(self, source: list[SourceKitSymbol]) -> SourceSymbolResolution:
        if len(source) != 1:
            return self._types.parse(source)
        symbol = source[0]
        if symbol.kind not in {SemanticSymbolKind.VARIABLE, SemanticSymbolKind.PROPERTY, SemanticSymbolKind.FIELD}:
            return SourceUnresolvedSymbol(reason="The inspected value has no supported semantic variable binding.")
        path = self._paths.parse(symbol.declaration_uri) if symbol.declaration_uri is not None else None
        if path is None or path.resolve() != self._source.path.resolve() or symbol.declaration_position is None:
            return SourceUnresolvedSymbol(reason="The value declaration is not available in the exact prepared document.")
        offset = self._offsets.resolve(self._source.content, symbol.declaration_position)
        annotation = self._annotations.parse(offset)
        position = self._positions.parse(annotation) if annotation is not None else None
        if position is None:
            return SourceUnresolvedSymbol(reason="The binding's type is inferred, composite, or otherwise unsupported for explicit semantic lookup.")
        return self._types.parse(self._document.lookup(position))
