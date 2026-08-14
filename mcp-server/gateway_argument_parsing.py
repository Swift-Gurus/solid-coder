"""Defines parsing of gateway command-line arguments."""

from typing import Protocol

from gateway_arguments import GatewayArguments


"""
solid-name: GatewayArgumentParsing
solid-category: abstraction
solid-description: Contract for parsing gateway command-line arguments.
"""
class GatewayArgumentParsing(Protocol):
    def parse(self, arguments: list[str]) -> GatewayArguments: ...
