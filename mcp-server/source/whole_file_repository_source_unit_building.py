"""Defines whole-file repository search entry construction."""

from typing import Protocol

from source.repository_source_snapshot import RepositorySourceSnapshot
from source.repository_source_unit import RepositorySourceUnit
from source.source_frontmatter import SourceFrontmatter


"""
solid-name: WholeFileRepositorySourceUnitBuilding
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for building whole-file repository search entries from source metadata.
"""
class WholeFileRepositorySourceUnitBuilding(Protocol):
    def build(
        self,
        snapshot: RepositorySourceSnapshot,
        frontmatter: SourceFrontmatter,
        index: int,
    ) -> RepositorySourceUnit: ...
