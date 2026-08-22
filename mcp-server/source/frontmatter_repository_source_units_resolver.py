"""Resolves whole-file searchable units from solid frontmatter."""

from source.repository_source_snapshot import RepositorySourceSnapshot
from source.repository_source_unit import RepositorySourceUnit
from source.repository_source_units_resolving import (
    RepositorySourceUnitsResolving,
)
from source.source_frontmatter import SourceFrontmatter
from source.source_frontmatter_reading import SourceFrontmatterReading
from source.whole_file_repository_source_unit_building import (
    WholeFileRepositorySourceUnitBuilding,
)


"""
solid-name: FrontmatterRepositorySourceUnitsResolver
solid-category: service
solid-spec: [SPEC-040]
solid-description: Resolves whole-file repository search entries from authored frontmatter.
"""
class FrontmatterRepositorySourceUnitsResolver(
    RepositorySourceUnitsResolving
):
    def __init__(
        self,
        frontmatter_reader: SourceFrontmatterReading,
        unit_builder: WholeFileRepositorySourceUnitBuilding,
    ) -> None:
        self._frontmatter_reader = frontmatter_reader
        self._unit_builder = unit_builder

    def resolve(
        self,
        snapshot: RepositorySourceSnapshot,
    ) -> list[RepositorySourceUnit]:
        frontmatters = self._frontmatter_reader.read(snapshot.content)
        if not frontmatters:
            frontmatters = [SourceFrontmatter()]
        return [
            self._unit_builder.build(snapshot, frontmatter, index)
            for index, frontmatter in enumerate(frontmatters)
        ]
