"""Defines execution of resolved gateway tools."""

from typing import Callable, Protocol


"""
solid-name: GatewayToolRunning
solid-category: abstraction
solid-description: Contract for executing one resolved gateway tool.
"""
class GatewayToolRunning(Protocol):
    def run(self, handler: Callable, tool_name: str, kwargs: dict) -> None: ...
