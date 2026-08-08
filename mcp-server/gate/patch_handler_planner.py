"""Plans applicable per-file handlers for one patch request."""

from exclusion_checking import ExclusionChecking
from extension_lookup import ExtensionLookup
from file_extension_extracting import FileExtensionExtracting
from hook_handling import HookHandling
from patch_file_handler_creating import PatchFileHandlerCreating
from patch_files_simulating import PatchFilesSimulating


"""
solid-name: PatchHandlerPlanner
solid-category: service
solid-description: Selects supported non-excluded patch simulations and creates their isolated review handlers.
solid-tags: [hook]
"""
class PatchHandlerPlanner:
    def __init__(
        self,
        simulator: PatchFilesSimulating,
        extension_lookup: ExtensionLookup,
        extension_extractor: FileExtensionExtracting,
        exclusion_checker: ExclusionChecking,
        handler_factory: PatchFileHandlerCreating,
    ) -> None:
        self._simulator = simulator
        self._extension_lookup = extension_lookup
        self._extension_extractor = extension_extractor
        self._exclusion_checker = exclusion_checker
        self._handler_factory = handler_factory

    def plan(self, tool_input: dict) -> list[HookHandling]:
        handlers: list[HookHandling] = []
        for simulation in self._simulator.simulate_all(tool_input):
            language = self._extension_lookup.language_for(
                self._extension_extractor.suffix_of(simulation.file_path)
            )
            if language is None or self._exclusion_checker.is_excluded(simulation.file_path):
                continue
            handlers.append(self._handler_factory.create(simulation, language))
        return handlers
