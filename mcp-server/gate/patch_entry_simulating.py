"""Defines simulation of one parsed file change."""

from typing import Protocol

from patch_file_simulation import PatchFileSimulation


"""
solid-name: PatchEntrySimulating
solid-category: abstraction
solid-description: Contract for producing post-change content and risk metadata for one file change.
solid-tags: [hook]
"""
class PatchEntrySimulating(Protocol):
    def simulate(self, entry: dict) -> PatchFileSimulation: ...
