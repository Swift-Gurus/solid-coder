"""Keeps native semantic calls outside the MCP server process."""

from harness.structured_model_decoding import StructuredModelDecoding
from json_rpc_response_building import JsonRpcResponseBuilding
from rpc_dispatching import RpcDispatching
from source.analysis.provenance.native.native_sourcekit_request import (
    NativeSourceKitRequest,
)
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing

"""
solid-name: NativeSourceKitDispatcher
solid-category: boundary-adapter
solid-spec: [SPEC-064]
solid-description: Serves correlated semantic queries over framed streams while keeping native-library failures isolated from the review engine.
"""


class NativeSourceKitDispatcher(RpcDispatching):
    def __init__(
        self,
        decoder: StructuredModelDecoding[NativeSourceKitRequest],
        requests: SourceSyntaxParsing[str, str],
        responses: JsonRpcResponseBuilding,
    ) -> None:
        self._decoder = decoder
        self._requests = requests
        self._responses = responses

    def dispatch(self, method: str, id: int | str | None, params: dict) -> dict | None:
        if id is None:
            return None
        if method != "native":
            return self._responses.error(
                id, -32601, "Unsupported native semantic method."
            )
        request = self._decoder.decode(
            {"id": id, "params": params}, "native semantic request"
        )
        try:
            result = self._requests.parse(request.payload)
        except (ValueError, ConnectionError, OSError) as error:
            return self._responses.error(id, -32603, str(error))
        return self._responses.success(id, result)
