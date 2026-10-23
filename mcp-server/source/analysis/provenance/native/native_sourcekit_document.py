"""Queries native cursor evidence on one previously opened source snapshot."""

import json
from pathlib import Path

from harness.structured_model_decoding import StructuredModelDecoding
from scoring.yaml_loader import YamlLoading
from source.analysis.provenance.native.native_sourcekit_cursor_info import (
    NativeSourceKitCursorInfo,
)
from source.analysis.provenance.stdio_rpc_channel import RpcExchanging
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing

"""
solid-name: NativeSourceKitDocument
solid-category: boundary-adapter
solid-spec: [SPEC-064]
solid-description: Resolves exact source offsets or semantic symbol identities within one native document session using the active compiler context.
"""


class NativeSourceKitDocument(
    SourceSyntaxParsing[int | str, NativeSourceKitCursorInfo]
):
    def __init__(
        self,
        path: Path,
        compiler_arguments: list[str],
        rpc: RpcExchanging,
        yaml: YamlLoading,
        decoder: StructuredModelDecoding[NativeSourceKitCursorInfo],
    ) -> None:
        self._path = path
        self._compiler_arguments = compiler_arguments
        self._rpc = rpc
        self._yaml = yaml
        self._decoder = decoder

    def parse(self, source: int | str) -> NativeSourceKitCursorInfo:
        selector = "key.offset" if isinstance(source, int) else "key.usr"
        payload = "\n".join(
            [
                "key.request: source.request.cursorinfo",
                f"key.sourcefile: {json.dumps(str(self._path))}",
                f"{selector}: {json.dumps(source)}",
                f"key.compilerargs: {json.dumps(self._compiler_arguments)}",
            ]
        )
        result = self._rpc.request("native", {"payload": payload})
        if not isinstance(result, str):
            raise ConnectionError(
                "The native semantic worker returned an invalid response."
            )
        return self._decoder.decode(
            self._yaml.safe_load(result), "native cursor evidence"
        )
