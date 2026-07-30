"""
solid-name: MCPServerFactory
solid-category: service
solid-description: Creates MCPServer instances with built-in defaults and injectable dependencies.
"""

from typing import Optional

from handler_store import HandlerStore
from handler_storing import HandlerStoring
from initialize_handler import InitializeHandler
from json_rpc_response_builder import JsonRpcResponseBuilder
from mcp_transport import MCPServer
from raw_stdin_source import RawStdinSource
from raw_stdout_sink import RawStdoutSink
from rpc_dispatcher import RpcDispatcher
from stdin_source import StdinSource
from stdio_incoming_messages import StdioIncomingMessages
from stdio_message_transport_runner import StdioMessageTransportRunner
from stdio_outgoing_message_factory import StdioOutgoingMessageFactory
from stdout_sink import StdoutSink
from tool_decorator import ToolDecorator
from tool_metadata_store import ToolMetadataStore
from tool_metadata_storing import ToolMetadataStoring
from tool_registrar import ToolRegistrar
from tool_result_formatter import ToolResultFormatter
from tools_call_handler import ToolsCallHandler
from tools_list_handler import ToolsListHandler
from transport_format_detector import TransportFormatDetector


class MCPServerFactory:

    def __init__(
        self,
        metadata: Optional[ToolMetadataStoring] = None,
        handlers: Optional[HandlerStoring] = None,
        stdin: Optional[StdinSource] = None,
        stdout: Optional[StdoutSink] = None,
    ) -> None:
        self._metadata = metadata or ToolMetadataStore()
        self._handlers = handlers or HandlerStore()
        self._stdin = stdin or RawStdinSource()
        self._stdout = stdout or RawStdoutSink()

    def build(self, name: str, version: str = "1.0.0") -> MCPServer:
        format_detector = TransportFormatDetector()
        tools_call_handler = ToolsCallHandler(self._handlers, ToolResultFormatter())
        dispatcher = RpcDispatcher(
            initialize_handler=InitializeHandler(name, version),
            tools_list_handler=ToolsListHandler(self._metadata),
            tools_call_handler=tools_call_handler,
            response_builder=JsonRpcResponseBuilder(),
        )
        transport_runner = StdioMessageTransportRunner(
            incoming=StdioIncomingMessages(self._stdin, format_detector),
            stdout=self._stdout,
            format_detector=format_detector,
            dispatcher=dispatcher,
            outgoing_factory=StdioOutgoingMessageFactory(),
        )
        return MCPServer(
            name=name,
            version=version,
            tool_registering=ToolDecorator(ToolRegistrar(self._metadata, self._handlers)),
            call_meta_provider=tools_call_handler,
            transport_runner=transport_runner,
        )
