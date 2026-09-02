from typing import Optional

from no_arg_rpc_handling import NoArgRpcHandling

_PROTOCOL_VERSION = "2024-11-05"


"""
solid-name: InitializeHandler
solid-category: service
solid-description: Provides server identification, capabilities, and model-facing guidance in response to initialization requests.
"""
class InitializeHandler(NoArgRpcHandling):

    def __init__(
        self,
        name: str,
        version: str,
        instructions: Optional[str] = None,
    ) -> None:
        self._name = name
        self._version = version
        self._instructions = instructions

    def handle(self) -> dict:
        response = {
            "protocolVersion": _PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": self._name, "version": self._version},
        }
        if self._instructions is not None:
            response["instructions"] = self._instructions
        return response
