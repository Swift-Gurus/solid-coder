"""Simulates the content resulting from one parsed file change."""

from patch_file_simulation import PatchFileSimulation
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
    ) -> None:
        self._parser = parser
        self._reader = file_reader

    def simulate(self, entry: dict) -> PatchFileSimulation:
        file_path = entry["path"]
        existing_content = ""
        low_risk = False
        if entry["operation"] == "add":
            content = self._parser.add_content(entry["lines"])
        else:
            try:
                existing_content = self._reader.read_text(file_path)
                content = self._parser.apply_update(existing_content, entry["lines"])
            except OSError:
                content = ""
                existing_content = ""
                low_risk = True
        return PatchFileSimulation(
            file_path=file_path,
            content=content,
            existing_content=existing_content,
            low_risk=low_risk,
        )
