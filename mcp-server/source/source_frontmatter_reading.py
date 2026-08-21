"""Defines typed source-frontmatter reading."""

from typing import Protocol

from source.source_frontmatter import SourceFrontmatter


"""
solid-name: SourceFrontmatterReading
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for reading ordered typed solid frontmatter blocks from source content.
"""
class SourceFrontmatterReading(Protocol):
    def read(self, content: str) -> list[SourceFrontmatter]: ...
