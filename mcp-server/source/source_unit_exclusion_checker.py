"""Checks exact reviewed-unit exclusions during repository search."""

from pathlib import Path

from harness.path_building import PathBuilding
from source.repository_source_unit import RepositorySourceUnit
from source.source_unit_exclusion_checking import SourceUnitExclusionChecking
from source.source_unit_identity import SourceUnitIdentity


"""
solid-name: SourceUnitExclusionChecker
solid-category: service
solid-spec: [SPEC-040]
solid-description: Matches repository units against exact reviewed-unit exclusions.
"""
class SourceUnitExclusionChecker(SourceUnitExclusionChecking):
    def __init__(self, paths: PathBuilding) -> None:
        self._paths = paths

    def is_excluded(
        self,
        project_root: Path,
        unit: RepositorySourceUnit,
        exclusions: list[SourceUnitIdentity],
    ) -> bool:
        return any(
            exclusion.unit_identity == unit.unit_identity
            and self._paths.build(project_root, exclusion.source_identity)
            == unit.path.resolve()
            for exclusion in exclusions
        )
