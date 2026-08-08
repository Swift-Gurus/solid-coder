"""Defines construction of per-file patch simulation results."""

from typing import Protocol

from patch_file_simulation import PatchFileSimulation


"""
solid-name: PatchFileSimulationCreating
solid-category: abstraction
solid-description: Contract for constructing a file-change simulation from derived content and risk values.
solid-tags: [hook]
"""
class PatchFileSimulationCreating(Protocol):
    def create(
        self,
        file_path: str,
        content: str,
        existing_content: str,
        low_risk: bool,
    ) -> PatchFileSimulation: ...
