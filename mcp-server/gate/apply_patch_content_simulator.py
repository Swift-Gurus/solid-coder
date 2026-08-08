"""Coordinates simulation of file content produced by apply_patch events."""

from patch_entry_selecting import PatchEntrySelecting
from patch_entry_simulating import PatchEntrySimulating
from patch_file_simulation import PatchFileSimulation


"""
solid-name: ApplyPatchContentSimulator
solid-category: service
solid-description: Coordinates selection and independent content simulation for every reviewable patch file.
solid-tags: [hook]
"""
class ApplyPatchContentSimulator:
    def __init__(
        self,
        entry_selector: PatchEntrySelecting,
        entry_simulator: PatchEntrySimulating,
    ) -> None:
        self._entry_selector = entry_selector
        self._entry_simulator = entry_simulator

    def simulate(self, tool_input: dict) -> tuple:
        simulations = self.simulate_all(tool_input)
        if not simulations:
            return "", "", True
        first = simulations[0]
        return first.content, first.existing_content, first.low_risk

    def simulate_all(self, tool_input: dict) -> list[PatchFileSimulation]:
        entries = self._entry_selector.select(tool_input.get("command", ""))
        return [self._entry_simulator.simulate(entry) for entry in entries]
