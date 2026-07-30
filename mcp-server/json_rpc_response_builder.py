"""
solid-name: JsonRpcResponseBuilder
solid-category: service
solid-description: Builds JSON-RPC 2.0 success and error response envelopes.
"""

from typing import Any

from json_rpc_response_building import JsonRpcResponseBuilding

_JSONRPC_VERSION = "2.0"


class JsonRpcResponseBuilder(JsonRpcResponseBuilding):

    def success(self, id: Any, result: Any) -> dict:
        return {"jsonrpc": _JSONRPC_VERSION, "id": id, "result": result}

    def error(self, id: Any, code: int, message: str) -> dict:
        return {"jsonrpc": _JSONRPC_VERSION, "id": id, "error": {"code": code, "message": message}}