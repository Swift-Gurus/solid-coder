"""Checks exact reviewed-unit exclusions during repository search."""

from pathlib import Path

from harness.path_building import PathBuilding
from source.repository_source_unit import RepositorySourceUnit
from source.search_target_granularity import SearchTargetGranularity
from source.source_operation_error import SourceOperationError
from source.source_unit import SourceUnit
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
        prepared_units: list[SourceUnit],
    ) -> bool:
        same_source = [
            exclusion
            for exclusion in exclusions
            if self._paths.build(project_root, exclusion.source_identity)
            == unit.path.resolve()
        ]
        if not same_source:
            return False
        if any(
            exclusion.granularity is SearchTargetGranularity.FILE
            for exclusion in same_source
        ):
            return True
        prepared_identities = {prepared.identity for prepared in prepared_units}
        if any(
            exclusion.unit_identity not in prepared_identities
            for exclusion in same_source
        ):
            raise SourceOperationError(
                f"Exact unit exclusion for '{unit.source_identity}' requires prepared source context "
                "from review.prepare or source.prepare_search_targets."
            )
        return any(
            exclusion.unit_identity == unit.unit_identity
            for exclusion in same_source
        )
