"""Provides configured pipeline tools to command-line clients."""

from pipeline.pipeline_tool_callables_creating import PipelineToolCallablesCreating


"""
solid-name: PipelineToolsProvider
solid-category: service
solid-description: Provides configured pipeline callables to command-line clients.
"""
class PipelineToolsProvider:
    def __init__(self, callables_factory: PipelineToolCallablesCreating) -> None:
        self._callables_factory = callables_factory

    def get(self) -> dict:
        return self._callables_factory.make_tool_callables().build()
