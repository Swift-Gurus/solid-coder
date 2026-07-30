"""
solid-name: ToolsListHandler
solid-category: service
solid-description: Provides the collection of available tools.
"""

from no_arg_rpc_handling import NoArgRpcHandling
from tool_metadata_storing import ToolMetadataStoring


class ToolsListHandler(NoArgRpcHandling):

    def __init__(self, metadata: ToolMetadataStoring) -> None:
        self._metadata = metadata

    def handle(self) -> dict:
        return {"tools": self._metadata.list_all()}
