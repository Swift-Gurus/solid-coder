"""Defines repository-unit projection from analyzed source."""

from typing import Protocol

from source.repository_source_snapshot import RepositorySourceSnapshot
from source.repository_source_unit import RepositorySourceUnit
from source.source_frontmatter import SourceFrontmatter
from source.source_unit import SourceUnit


"""
solid-name: RepositorySourceUnitProjecting
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for projecting analyzed units into searchable repository units.
"""
class RepositorySourceUnitProjecting(Protocol):
    def project(
        self,
        snapshot: RepositorySourceSnapshot,
        unit: SourceUnit,
        frontmatters: list[SourceFrontmatter],
    ) -> RepositorySourceUnit: ...
