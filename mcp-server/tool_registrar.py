"""
solid-name: ToolRegistrar
solid-category: service
solid-description: Registers tools with their configuration and behavior.
"""

from typing import Callable, Optional

from handler_storing import HandlerStoring
from tool_metadata_storing import ToolMetadataStoring
from tool_registering import ToolRegistering


class ToolRegistrar(ToolRegistering):

    def __init__(self, metadata: ToolMetadataStoring, handlers: HandlerStoring) -> None:
        self._metadata = metadata
        self._handlers = handlers

    def register(
        self, name: str, description: str, input_schema: dict, handler: Callable, meta: Optional[dict] = None
    ) -> None:
        self._metadata.add_metadata(name, description, input_schema, meta)
        self._handlers.add_handler(name, handler)
