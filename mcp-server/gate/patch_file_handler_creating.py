"""Defines construction of handlers for simulated patch files."""

from typing import Protocol

from hook_handling import HookHandling
from patch_file_simulation import PatchFileSimulation


"""
solid-name: PatchFileHandlerCreating
solid-category: abstraction
solid-description: Contract for constructing an isolated review handler for one simulated file change.
solid-tags: [hook]
"""
class PatchFileHandlerCreating(Protocol):
    def create(
        self,
        simulation: PatchFileSimulation,
        language: str,
    ) -> HookHandling: ...
