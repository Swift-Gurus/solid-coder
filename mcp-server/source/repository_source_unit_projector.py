"""Projects analyzed source units into repository-search units."""

from source.repository_source_snapshot import RepositorySourceSnapshot
from source.repository_source_unit import RepositorySourceUnit
from source.repository_source_unit_projecting import (
    RepositorySourceUnitProjecting,
)
from source.source_frontmatter import SourceFrontmatter
from source.source_frontmatter_selecting import SourceFrontmatterSelecting
from source.source_slice_resolving import SourceSliceResolving
from source.source_unit import SourceUnit

_MISSING_DESCRIPTION = "No solid-description frontmatter."


"""
solid-name: RepositorySourceUnitProjector
solid-category: service
solid-spec: [SPEC-040]
solid-description: Projects analyzed source and metadata into independently searchable repository units.
"""
class RepositorySourceUnitProjector(RepositorySourceUnitProjecting):
    def __init__(
        self,
        frontmatter: SourceFrontmatterSelecting,
        source_slice: SourceSliceResolving,
    ) -> None:
        self._frontmatter = frontmatter
        self._source_slice = source_slice

    def project(
        self,
        snapshot: RepositorySourceSnapshot,
        unit: SourceUnit,
        frontmatters: list[SourceFrontmatter],
    ) -> RepositorySourceUnit:
        frontmatter = self._frontmatter.select(unit, frontmatters)
        return RepositorySourceUnit(
            unit=unit.name,
            unit_identity=unit.identity,
            description=frontmatter.description or _MISSING_DESCRIPTION,
            path=snapshot.path,
            source_identity=snapshot.source_identity,
            start_offset=unit.start_offset,
            end_offset=unit.end_offset,
            content=self._source_slice.resolve(
                snapshot.content,
                unit.start_offset,
                unit.end_offset,
            ),
            frontmatter=frontmatter,
            file_content=snapshot.content,
            content_sha256=snapshot.content_sha256,
        )
