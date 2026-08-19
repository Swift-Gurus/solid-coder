"""Reads added destination lines for one tracked source path."""

from pathlib import Path

from source.added_line_ranges_parsing import AddedLineRangesParsing
from source.added_line_ranges_reading import AddedLineRangesReading
from source.git_process_execution import GitProcessExecution
from source.git_querying import GitQuerying
from source.source_line_range import SourceLineRange


"""
solid-name: GitAddedLineRangesReader
solid-category: service
solid-spec: [SPEC-040]
solid-description: Reads and parses destination-coordinate added ranges for one tracked Git path.
"""
class GitAddedLineRangesReader(AddedLineRangesReading):
    def __init__(
        self,
        git: GitQuerying,
        parser: AddedLineRangesParsing,
    ) -> None:
        self._git = git
        self._parser = parser

    def read(
        self,
        project_root: Path,
        paths: list[str],
    ) -> list[SourceLineRange]:
        diff = self._git.query(
            project_root,
            GitProcessExecution(
                ["diff", "--unified=0", "HEAD", "--", *paths]
            ),
            f"reading added lines for '{', '.join(paths)}'",
        )
        return self._parser.parse(diff)
