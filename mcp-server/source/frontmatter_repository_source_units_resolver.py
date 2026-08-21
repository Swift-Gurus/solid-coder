"""Resolves searchable units from solid frontmatter blocks."""

from source.repository_source_snapshot import RepositorySourceSnapshot
from source.repository_source_unit import RepositorySourceUnit
from source.repository_source_units_resolving import (
    RepositorySourceUnitsResolving,
)
from source.source_frontmatter import SourceFrontmatter
from source.source_frontmatter_reading import SourceFrontmatterReading

_MISSING_DESCRIPTION = "No solid-description frontmatter."


"""
solid-name: FrontmatterRepositorySourceUnitsResolver
solid-category: service
solid-spec: [SPEC-040]
solid-description: Resolves searchable repository units from typed solid frontmatter metadata.
"""
class FrontmatterRepositorySourceUnitsResolver(
    RepositorySourceUnitsResolving
):
    def __init__(
        self,
        frontmatter_reader: SourceFrontmatterReading,
    ) -> None:
        self._frontmatter_reader = frontmatter_reader

    def resolve(
        self,
        snapshot: RepositorySourceSnapshot,
    ) -> list[RepositorySourceUnit]:
        frontmatters = self._frontmatter_reader.read(snapshot.content)
        if not frontmatters:
            return [RepositorySourceUnit(
                unit=snapshot.path.name,
                description=_MISSING_DESCRIPTION,
                path=snapshot.path,
                source_identity=snapshot.source_identity,
                frontmatter=SourceFrontmatter(),
                file_content=snapshot.content,
                content_sha256=snapshot.content_sha256,
            )]

        return [
            RepositorySourceUnit(
                unit=frontmatter.name or snapshot.path.name,
                description=frontmatter.description or _MISSING_DESCRIPTION,
                path=snapshot.path,
                source_identity=snapshot.source_identity,
                frontmatter=frontmatter,
                file_content=snapshot.content,
                content_sha256=snapshot.content_sha256,
            )
            for frontmatter in frontmatters
        ]
