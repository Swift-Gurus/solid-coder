"""
solid-description: Contract for creating a coordinator from a gate.
solid-category: abstraction
solid-tags: [hook]
"""

from typing import Protocol

from hook_utils import GateHandling
from coordinator_running import CoordinatorRunning


class CoordinatorMaking(Protocol):
    def make_coordinator(self, gate: GateHandling) -> CoordinatorRunning: ...
