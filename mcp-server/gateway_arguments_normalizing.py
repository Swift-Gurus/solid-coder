"""Defines normalization of parsed gateway arguments."""

from typing import Protocol

from gateway_arguments import GatewayArguments


"""
solid-name: GatewayArgumentsNormalizing
solid-category: abstraction
solid-description: Contract for applying gateway command compatibility rules to parsed arguments.
"""
class GatewayArgumentsNormalizing(Protocol):
    def normalize(self, arguments: GatewayArguments) -> GatewayArguments: ...
