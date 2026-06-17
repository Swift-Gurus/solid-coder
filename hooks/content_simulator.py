"""
solid-description: Dispatches tool events to the appropriate per-tool content simulator.
solid-category: service
solid-tags: [hook]
"""

from typing import Protocol


class ToolHandling(Protocol):
    def simulate(self, tool_input: dict) -> tuple: ...


class ContentSimulator:
    """Facade: dispatches simulate() calls to the matching per-tool handler."""

    def __init__(self, handlers: dict) -> None:
        self._handlers = handlers

    def simulate(self, tool_name: str, tool_input: dict) -> tuple:
        handler = self._handlers.get(tool_name)
        if handler is None:
            return "", "", True
        return handler.simulate(tool_input)
