"""Selects source frontmatter for analyzed units."""

from source.source_frontmatter import SourceFrontmatter
from source.source_frontmatter_selecting import SourceFrontmatterSelecting
from source.source_unit import SourceUnit


"""
solid-name: SourceFrontmatterSelector
solid-category: service
solid-spec: [SPEC-040]
solid-description: Matches analyzed source units with their authored frontmatter.
"""
class SourceFrontmatterSelector(SourceFrontmatterSelecting):
    def select(
        self,
        unit: SourceUnit,
        frontmatters: list[SourceFrontmatter],
    ) -> SourceFrontmatter:
        return next(
            (
                frontmatter
                for frontmatter in frontmatters
                if frontmatter.name == unit.name
            ),
            SourceFrontmatter(),
        )
