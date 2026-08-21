"""Defines CLI-facing codebase-search serialization."""

from typing import Protocol

from source.source_search_output import SourceSearchOutput


"""
solid-name: CodebaseSearchOutputSerializing
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for serializing typed source-search results at the CLI JSON boundary.
"""
class CodebaseSearchOutputSerializing(Protocol):
    def serialize(self, output: SourceSearchOutput) -> dict: ...
