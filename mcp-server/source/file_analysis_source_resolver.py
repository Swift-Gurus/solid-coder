"""Resolves accessible file-backed source content."""

from source.file_analysis_source import FileAnalysisSource
from source.file_analysis_source_resolving import FileAnalysisSourceResolving
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
    def __init__(self, reader: TextFileReading) -> None:
        self._reader = reader

    def resolve(
        self,
        source: FileAnalysisSource,
    ) -> ResolvedAnalysisSource:
        path = source.path.resolve()
        content = self._reader.read(path)
        if content is None:
            raise SourceOperationError(
                f"Unable to read source analysis file '{path}'"
            )
        return ResolvedAnalysisSource(identity=str(path), text=content)
