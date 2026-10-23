"""Converts verified semantic symbol evidence into ownership inputs."""

from pathlib import Path

from pydantic import FileUrl
from source.analysis.provenance.semantic_symbol_kind import SemanticSymbolKind
from source.analysis.provenance.source_declaration_symbol import SourceDeclarationSymbol
from source.analysis.provenance.source_sdk_symbol import SourceSDKSymbol
from source.analysis.provenance.source_symbol_provenance import SourceSymbolResolution
from source.analysis.provenance.source_unresolved_symbol import SourceUnresolvedSymbol
from source.analysis.provenance.sourcekit_symbol import SourceKitSymbol
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing

"""
solid-name: SourceKitSymbolResolutionParser
solid-category: boundary-adapter
solid-spec: [SPEC-064]
solid-description: Interprets semantic declaration evidence while preserving missing or ambiguous symbol resolution.
"""


class SourceKitSymbolResolutionParser(
    SourceSyntaxParsing[list[SourceKitSymbol], SourceSymbolResolution]
):
    def __init__(
        self,
        allowed_kinds: frozenset[SemanticSymbolKind],
        paths: SourceSyntaxParsing[FileUrl, Path | None],
    ) -> None:
        self._allowed_kinds = allowed_kinds
        self._paths = paths

    def parse(self, source: list[SourceKitSymbol]) -> SourceSymbolResolution:
        if not source:
            return SourceUnresolvedSymbol(
                reason="The semantic service did not resolve a symbol."
            )
        if len(source) != 1:
            return SourceUnresolvedSymbol(
                kind="ambiguous",
                reason="The semantic service returned multiple symbols.",
            )
        symbol = source[0]
        if not symbol.symbol_id:
            return SourceUnresolvedSymbol(
                reason="The semantic service omitted the symbol identity."
            )
        if self._allowed_kinds and symbol.kind not in self._allowed_kinds:
            return SourceUnresolvedSymbol(
                reason="The semantic service did not establish the requested symbol category."
            )
        if symbol.is_system is True:
            return SourceSDKSymbol(
                symbol_id=symbol.symbol_id,
                evidence="The semantic service identifies this symbol as SDK-owned (isSystem=true).",
            )
        path = (
            self._paths.parse(symbol.declaration_uri)
            if symbol.declaration_uri is not None
            else None
        )
        if path is None:
            return SourceUnresolvedSymbol(
                reason="The semantic service supplied neither SDK proof nor a local declaration."
            )
        if path.suffix == ".swiftinterface":
            return SourceUnresolvedSymbol(
                reason="A generated interface location does not establish the original declaration location."
            )
        return SourceDeclarationSymbol(
            symbol_id=symbol.symbol_id, declaration_path=path
        )
