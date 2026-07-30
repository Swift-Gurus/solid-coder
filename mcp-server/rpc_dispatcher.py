"""
solid-name: RpcDispatcher
solid-category: service
solid-description: Processes JSON-RPC method requests and returns properly formatted responses.
"""

from typing import Any, Optional

from json_rpc_response_building import JsonRpcResponseBuilding
from no_arg_rpc_handling import NoArgRpcHandling
from rpc_dispatching import RpcDispatching
from tools_call_handling import ToolsCallHandling

_UNKNOWN_METHOD_CODE = -32601
_UNKNOWN_TOOL_CODE = -32601


class RpcDispatcher(RpcDispatching):

    def __init__(
        self,
        initialize_handler: NoArgRpcHandling,
        tools_list_handler: NoArgRpcHandling,
        tools_call_handler: ToolsCallHandling,
        response_builder: JsonRpcResponseBuilding,
    ) -> None:
        self._initialize_handler = initialize_handler
        self._tools_list_handler = tools_list_handler
        self._tools_call_handler = tools_call_handler
        self._response_builder = response_builder

    def dispatch(self, method: str, id: Any, params: dict) -> Optional[dict]:
        if id is None:
            return None
        if method == "initialize":
            return self._response_builder.success(id, self._initialize_handler.handle())
        if method == "tools/list":
            return self._response_builder.success(id, self._tools_list_handler.handle())
        if method == "tools/call":
            return self._dispatch_tool_call(id, params)
        return self._response_builder.error(id, _UNKNOWN_METHOD_CODE, f"Unknown method: {method}")

    def _dispatch_tool_call(self, id: Any, params: dict) -> dict:
        name = params.get("name", "")
        try:
            result = self._tools_call_handler.handle(name, params.get("arguments", {}), params.get("_meta"))
        except LookupError:
            return self._response_builder.error(id, _UNKNOWN_TOOL_CODE, f"Unknown tool: {name}")
        return self._response_builder.success(id, result)
