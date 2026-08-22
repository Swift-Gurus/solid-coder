"""Builds whole-file repository search entries."""

from source.repository_source_snapshot import RepositorySourceSnapshot
from source.repository_source_unit import RepositorySourceUnit
from source.source_frontmatter import SourceFrontmatter
from source.whole_file_repository_source_unit_building import (
    WholeFileRepositorySourceUnitBuilding,
)

_MISSING_DESCRIPTION = "No solid-description frontmatter."


"""
solid-name: WholeFileRepositorySourceUnitBuilder
solid-category: service
solid-spec: [SPEC-040]
solid-description: Builds searchable whole-file entries while preserving frontmatter provenance.
"""
class WholeFileRepositorySourceUnitBuilder(
    WholeFileRepositorySourceUnitBuilding
):
    def build(
        self,
        snapshot: RepositorySourceSnapshot,
        frontmatter: SourceFrontmatter,
        index: int,
    ) -> RepositorySourceUnit:
        unit_name = frontmatter.name or snapshot.path.name
        return RepositorySourceUnit(
            unit=unit_name,
            unit_identity=f"frontmatter:{unit_name}:{index}",
            description=frontmatter.description or _MISSING_DESCRIPTION,
            path=snapshot.path,
            source_identity=snapshot.source_identity,
            start_offset=0,
            end_offset=max(0, len(snapshot.content.encode("utf-8")) - 1),
            content=snapshot.content,
            frontmatter=frontmatter,
            file_content=snapshot.content,
            content_sha256=snapshot.content_sha256,
        )
