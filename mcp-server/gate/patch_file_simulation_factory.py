"""Constructs per-file patch simulation results."""

from patch_file_simulation import PatchFileSimulation


"""
solid-name: PatchFileSimulationFactory
solid-category: factory
solid-description: Constructs immutable file-change simulations from derived content and risk values.
solid-tags: [hook]
"""
class PatchFileSimulationFactory:
    def create(
        self,
        file_path: str,
        content: str,
        existing_content: str,
        low_risk: bool,
    ) -> PatchFileSimulation:
        return PatchFileSimulation(
            file_path=file_path,
            content=content,
            existing_content=existing_content,
            low_risk=low_risk,
        )
