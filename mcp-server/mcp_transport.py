"""
solid-name: MCPServer
solid-category: service
solid-description: Provides the public interface for an MCP server, enabling tool registration, metadata access, and transport execution.

Public API preserved for all four solid-coder MCP servers: server.tool(...) decorator + server.run().
"""

from typing import Any, Optional

from call_meta_providing import CallMetaProviding
from mcp_server_registering import MCPServerRegistering
from message_transport_running import MessageTransportRunning


class MCPServer:

    def __init__(
        self,
        name: str,
        version: str,
        tool_registering: MCPServerRegistering,
        call_meta_provider: CallMetaProviding,
        transport_runner: MessageTransportRunning,
    ) -> None:
        self.name = name
        self.version = version
        self._tool_registering = tool_registering
        self._call_meta_provider = call_meta_provider
        self._transport_runner = transport_runner

    def tool(self, name: str, description: str, input_schema: dict, meta: Optional[dict] = None) -> Any:
        return self._tool_registering.tool(name, description, input_schema, meta)

    def get_current_call_meta(self) -> dict:
        return self._call_meta_provider.get_current_call_meta()

    def run(self) -> None:
        self._transport_runner.run()
