"""Resolves the complete range of a readable text file."""

from pathlib import Path

from source.source_line_range import SourceLineRange
from source.source_operation_error import SourceOperationError
from source.whole_file_range_resolving import WholeFileRangeResolving
from utils.prompt_builder import TextFileReading


"""
solid-name: ReadableWholeFileRangeResolver
solid-category: service
solid-spec: [SPEC-040]
solid-description: Resolves the complete inclusive line range of a readable text file.
"""
class ReadableWholeFileRangeResolver(WholeFileRangeResolving):
    def __init__(self, reader: TextFileReading) -> None:
        self._reader = reader

    def resolve(self, path: Path) -> list[SourceLineRange]:
        content = self._reader.read(path)
        if content is None:
            raise SourceOperationError(f"Could not read changed file '{path}'")
        line_count = len(content.splitlines())
        if line_count == 0:
            return []
        return [SourceLineRange(start=1, end=line_count)]
