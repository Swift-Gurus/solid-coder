"""Handles one parsed non-patch write-gate request."""

from coordinator_making import CoordinatorMaking
from exclusion_checking import ExclusionChecking
from extension_lookup import ExtensionLookup
from file_extension_extracting import FileExtensionExtracting
from gate_handling import GateHandling


"""
solid-name: StandardWriteRequestHandler
solid-category: service
solid-description: Applies file eligibility policy and delegates an ordinary write or edit to the existing coordinator.
solid-tags: [hook]
"""
class StandardWriteRequestHandler:
    def __init__(
        self,
        gate: GateHandling,
        extension_lookup: ExtensionLookup,
        extension_extractor: FileExtensionExtracting,
        exclusion_checker: ExclusionChecking,
        coordinator_maker: CoordinatorMaking,
    ) -> None:
        self._gate = gate
        self._extension_lookup = extension_lookup
        self._extension_extractor = extension_extractor
        self._exclusion_checker = exclusion_checker
        self._coordinator_maker = coordinator_maker

    def handle(self, parsed: tuple) -> None:
        tool_name, tool_input, file_path, session_id, cwd = parsed
        language = self._extension_lookup.language_for(
            self._extension_extractor.suffix_of(file_path)
        )
        if language is None or self._exclusion_checker.is_excluded(file_path):
            self._gate.allow()
            return
        self._coordinator_maker.make_coordinator(self._gate).run(
            tool_name,
            tool_input,
            file_path,
            language,
            session_id,
            cwd,
        )
