"""Defines validation of arguments for resolved gateway tools."""

from typing import Callable, Protocol


"""
solid-name: GatewayArgumentValidating
solid-category: abstraction
solid-description: Contract for validating arguments accepted by a resolved gateway tool.
"""
class GatewayArgumentValidating(Protocol):
    def validate(self, handler: Callable, tool_name: str, kwargs: dict) -> None: ...
