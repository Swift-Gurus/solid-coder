"""Defines command-line output for successful gateway execution."""

from typing import Protocol


"""
solid-name: GatewayOutputWriting
solid-category: abstraction
solid-description: Contract for writing successful gateway command results.
"""
class GatewayOutputWriting(Protocol):
    def write_result(self, result: object) -> None: ...
