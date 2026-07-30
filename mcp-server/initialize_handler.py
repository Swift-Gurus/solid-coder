"""
solid-name: InitializeHandler
solid-category: service
solid-description: Provides server identification and capabilities in response to initialization requests.
"""

from no_arg_rpc_handling import NoArgRpcHandling

_PROTOCOL_VERSION = "2024-11-05"


class InitializeHandler(NoArgRpcHandling):

    def __init__(self, name: str, version: str) -> None:
        self._name = name
        self._version = version

    def handle(self) -> dict:
        return {
            "protocolVersion": _PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": self._name, "version": self._version},
        }
