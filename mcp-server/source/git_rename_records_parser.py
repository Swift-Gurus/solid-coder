"""Parses ordered rename identities from Git output."""

from source.git_rename_records_parsing import GitRenameRecordsParsing
from source.renamed_source_path import RenamedSourcePath
from source.source_operation_error_creating import SourceOperationErrorCreating


"""
solid-name: GitRenameRecordsParser
solid-category: boundary
solid-spec: [SPEC-040]
solid-description: Parses validated previous and destination path identities from NUL-delimited Git rename output.
"""
class GitRenameRecordsParser(GitRenameRecordsParsing):
    def __init__(
        self,
        error_factory: SourceOperationErrorCreating,
    ) -> None:
        self._error_factory = error_factory

    def parse(self, output: str) -> list[RenamedSourcePath]:
        tokens = [token for token in output.split("\0") if token]
        if len(tokens) % 3 != 0:
            raise self._error_factory.create(
                "Git returned an invalid rename record"
            )
        renames = [
            RenamedSourcePath(
                previous_path=tokens[index + 1],
                path=tokens[index + 2],
            )
            for index in range(0, len(tokens), 3)
        ]
        return sorted(renames, key=lambda rename: rename.path)
