"""Queries semantic symbols on one exact open document."""

from pathlib import Path
from typing import Protocol

from harness.structured_model_decoding import StructuredModelDecoding
from source.analysis.provenance.native.source_call_reference import SourceCallReference
from source.analysis.provenance.semantic_position import SemanticPosition
from source.analysis.provenance.source_symbol_provenance import SourceSymbolResolution
from source.analysis.provenance.sourcekit_symbol import SourceKitSymbol
from source.analysis.provenance.stdio_rpc_channel import RpcExchanging
from source.analysis.provenance.utf16_source_position_resolver import (
    SourceCoordinateResolving,
)
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing

"""
solid-name: SemanticSymbolLookingUp
solid-category: abstraction
solid-spec: [SPEC-064]
solid-description: Contract for resolving semantic symbols at an open document's byte offset.
"""


class SemanticSymbolLookingUp(Protocol):
    def lookup(self, offset: int) -> list[SourceKitSymbol]: ...
    def return_type(self, reference: SourceCallReference) -> SourceSymbolResolution: ...


"""
solid-name: SourceKitDocument
solid-category: boundary-adapter
solid-spec: [SPEC-064]
solid-description: Resolves semantic symbols at exact source positions in an open Swift document.
"""


class SourceKitDocument(SemanticSymbolLookingUp):
    def __init__(
        self,
        path: Path,
        source: str,
        rpc: RpcExchanging,
        positions: SourceCoordinateResolving[int, SemanticPosition],
        decoder: StructuredModelDecoding[list[SourceKitSymbol]],
        return_types: SourceSyntaxParsing[SourceCallReference, SourceSymbolResolution],
    ) -> None:
        self._path = path
        self._source = source
        self._rpc = rpc
        self._positions = positions
        self._decoder = decoder
        self._return_types = return_types

    def lookup(self, offset: int) -> list[SourceKitSymbol]:
        position = self._positions.resolve(self._source, offset)
        result = self._rpc.request(
            "textDocument/symbolInfo",
            {
                "textDocument": {"uri": self._path.as_uri()},
                "position": position.model_dump(mode="json"),
            },
        )
        return self._decoder.decode(
            [] if result is None else result, "semantic symbols"
        )

    def return_type(self, reference: SourceCallReference) -> SourceSymbolResolution:
        return self._return_types.parse(reference)
