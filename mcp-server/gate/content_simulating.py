from typing import Protocol

from simulated_write import SimulatedWrite


"""
solid-name: ContentSimulating
solid-description: Contract for simulating the prospective content and review context of a write operation.
solid-category: abstraction
solid-tags: [hook]
"""
class ContentSimulating(Protocol):
    def simulate(self, tool_name: str, tool_input: dict) -> SimulatedWrite: ...
