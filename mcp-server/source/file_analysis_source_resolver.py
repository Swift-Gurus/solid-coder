"""Resolves accessible file-backed source content."""

from collections.abc import Callable
from pathlib import Path

from gate.file_extension_extracting import FileExtensionExtracting
from source.file_analysis_source import FileAnalysisSource
from source.file_analysis_source_resolving import FileAnalysisSourceResolving
from source.repository_target_resolver import RepositoryTargetResolving
from source.resolved_analysis_source import ResolvedAnalysisSource
from source.source_operation_error import SourceOperationError
from utils.prompt_builder import TextFileReading

"""
solid-name: FileAnalysisSourceResolver
solid-category: service
solid-spec: [SPEC-040]
solid-description: Reads and normalizes one accessible file-backed analysis source.
"""


class FileAnalysisSourceResolver(FileAnalysisSourceResolving):
    def __init__(
        self,
        reader: TextFileReading,
        extension_extractor: FileExtensionExtracting,
        targets: RepositoryTargetResolving,
        current_directory: Callable[[], Path],
    ) -> None:
        self._reader = reader
        self._extension_extractor = extension_extractor
        self._targets = targets
        self._current_directory = current_directory

    def resolve(
        self,
        source: FileAnalysisSource,
    ) -> ResolvedAnalysisSource:
        path = self._targets.resolve(self._current_directory(), source.path)
        content = self._reader.read(path)
        if content is None:
            raise SourceOperationError(f"Unable to read source analysis file '{path}'")
        return ResolvedAnalysisSource(
            identity=str(path),
            file_extension=self._extension_extractor.suffix_of(str(path)).lower(),
            text=content,
        )
