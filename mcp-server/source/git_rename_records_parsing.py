"""Defines parsing of Git rename records."""

from typing import Protocol

from source.renamed_source_path import RenamedSourcePath


"""
solid-name: GitRenameRecordsParsing
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for parsing ordered previous and destination paths from Git rename output.
"""
class GitRenameRecordsParsing(Protocol):
    def parse(self, output: str) -> list[RenamedSourcePath]: ...
