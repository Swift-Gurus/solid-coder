"""Coordinates simulation of file content produced by apply_patch events."""

from patch_entry_selecting import PatchEntrySelecting
from patch_entry_simulating import PatchEntrySimulating
from patch_file_simulation import PatchFileSimulation


"""
solid-name: ApplyPatchContentSimulator
solid-category: service
solid-description: Coordinates prospective content simulation for every file in one apply-patch request.
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

    def simulate_all(self, tool_input: dict) -> list[PatchFileSimulation]:
        entries = self._entry_selector.select(tool_input.get("command", ""))
        return [self._entry_simulator.simulate(entry) for entry in entries]
