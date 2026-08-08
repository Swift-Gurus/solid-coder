"""Defines simulation of every reviewable file in one patch."""

from typing import Protocol

from patch_file_simulation import PatchFileSimulation


"""
solid-name: PatchFilesSimulating
solid-category: abstraction
solid-description: Contract for producing independent simulations for every reviewable file change.
solid-tags: [hook]
"""
class PatchFilesSimulating(Protocol):
    def simulate_all(self, tool_input: dict) -> list[PatchFileSimulation]: ...
