"""Defines source-frontmatter selection for one analyzed unit."""

from typing import Protocol

from source.source_frontmatter import SourceFrontmatter
from source.source_unit import SourceUnit


"""
solid-name: SourceFrontmatterSelecting
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for selecting source frontmatter associated with an analyzed source unit.
"""
class SourceFrontmatterSelecting(Protocol):
    def select(
        self,
        unit: SourceUnit,
        frontmatters: list[SourceFrontmatter],
    ) -> SourceFrontmatter: ...
