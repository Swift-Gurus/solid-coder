"""
solid-description: Contract for simulating the resulting content of a tool invocation.
solid-category: abstraction
solid-tags: [hook]
"""

from typing import Protocol


class ContentSimulating(Protocol):
    def simulate(self, tool_name: str, tool_input: dict) -> tuple: ...
