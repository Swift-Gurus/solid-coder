"""Queries semantic symbols on one exact open document."""

from pathlib import Path
from typing import Protocol

from harness.structured_model_decoding import StructuredModelDecoding
from source.analysis.provenance.semantic_position import SemanticPosition
from source.analysis.provenance.sourcekit_symbol import SourceKitSymbol
from source.analysis.provenance.stdio_rpc_channel import RpcExchanging
from source.analysis.provenance.utf16_source_position_resolver import SourceCoordinateResolving


"""
solid-name: SemanticSymbolLookingUp
solid-category: abstraction
solid-spec: [SPEC-064]
solid-description: Contract for resolving semantic symbols at an open document's byte offset.
"""
class SemanticSymbolLookingUp(Protocol):
    def lookup(self, offset: int) -> list[SourceKitSymbol]: ...


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
    ) -> None:
        self._path = path
        self._source = source
        self._rpc = rpc
        self._positions = positions
        self._decoder = decoder

    def lookup(self, offset: int) -> list[SourceKitSymbol]:
        position = self._positions.resolve(self._source, offset)
        result = self._rpc.request("textDocument/symbolInfo", {
            "textDocument": {"uri": self._path.as_uri()},
            "position": position.model_dump(mode="json"),
        })
        return self._decoder.decode([] if result is None else result, "semantic symbols")
