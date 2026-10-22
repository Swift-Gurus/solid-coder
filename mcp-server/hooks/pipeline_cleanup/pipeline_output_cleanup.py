"""Executes cleanup through injected output and filesystem capabilities."""

from typing import Protocol, TextIO

from directory_removing import DirectoryRemoving
from hc_config_debug_reader import DebugModeReading
from output_path_safety_checking import OutputPathSafetyChecking
from transcript_output_roots_reading import TranscriptOutputRootsReading


"""
solid-name: PipelineOutputCleaning
solid-category: abstraction
solid-description: Contract for safely cleaning pipeline outputs associated with a session transcript.
"""
class PipelineOutputCleaning(Protocol):
    def clean(self, transcript_path: str) -> None: ...


"""
solid-name: PipelineOutputCleanup
solid-category: service
solid-description: Removes eligible pipeline outputs while preserving debug artifacts and reporting unsafe locations.
"""
class PipelineOutputCleanup(PipelineOutputCleaning):
    def __init__(
        self,
        debug_reader: DebugModeReading,
        roots_reader: TranscriptOutputRootsReading,
        path_safety: OutputPathSafetyChecking,
        remover: DirectoryRemoving,
        diagnostics: TextIO,
    ) -> None:
        self._debug_reader = debug_reader
        self._roots_reader = roots_reader
        self._path_safety = path_safety
        self._remover = remover
        self._diagnostics = diagnostics

    def clean(self, transcript_path: str) -> None:
        if self._debug_reader.is_debug():
            return
        for root in self._roots_reader(transcript_path):
            if self._path_safety(root):
                self._remover(root, ignore_errors=True)
            else:
                self._diagnostics.write(
                    f"cleanup_pipeline_output: skipping unsafe path {root!r}\n"
                )
