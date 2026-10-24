"""
solid-name: ToolRegistrar
solid-category: service
solid-description: Registers tools with their configuration and behavior.
"""

from collections.abc import Callable

from handler_storing import HandlerStoring
from tool_metadata_storing import ToolMetadataStoring
from tool_registering import ToolRegistering


class ToolRegistrar(ToolRegistering):
    def __init__(
        self,
        metadata: ToolMetadataStoring,
        handlers: HandlerStoring,
        enabled_tools: frozenset[str] | None = None,
    ) -> None:
        self._metadata = metadata
        self._handlers = handlers
        self._enabled_tools = enabled_tools

    def register(
        self,
        name: str,
        description: str,
        input_schema: dict,
        handler: Callable,
        meta: dict | None = None,
    ) -> None:
        if self._enabled_tools is not None and name not in self._enabled_tools:
            return
        self._metadata.add_metadata(name, description, input_schema, meta)
        self._handlers.add_handler(name, handler)
