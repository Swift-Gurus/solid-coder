"""Simulates the content resulting from one parsed file change."""

from patch_file_simulation import PatchFileSimulation
from patch_file_simulation_creating import PatchFileSimulationCreating
from patch_parsing import PatchParsing
from path_file_system_reader import FileSystemReading


"""
solid-name: PatchEntrySimulator
solid-category: service
solid-description: Derives post-change content and risk metadata for one added or updated file.
solid-tags: [hook]
"""
class PatchEntrySimulator:
    def __init__(
        self,
        parser: PatchParsing,
        file_reader: FileSystemReading,
        result_factory: PatchFileSimulationCreating,
    ) -> None:
        self._parser = parser
        self._reader = file_reader
        self._result_factory = result_factory

    def simulate(self, entry: dict) -> PatchFileSimulation:
        file_path = entry["path"]
        if entry["operation"] == "add":
            return self._result_factory.create(
                file_path=file_path,
                content=self._parser.add_content(entry["lines"]),
                existing_content="",
                low_risk=False,
            )
        try:
            existing = self._reader.read_text(file_path)
            return self._result_factory.create(
                file_path=file_path,
                content=self._parser.apply_update(existing, entry["lines"]),
                existing_content=existing,
                low_risk=False,
            )
        except OSError:
            return self._result_factory.create(
                file_path=file_path,
                content="",
                existing_content="",
                low_risk=True,
            )
