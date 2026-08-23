"""Coordinates typed repository source search."""

from pathlib import Path
from typing import Callable

from source.repository_source_snapshots_collecting import (
    RepositorySourceSnapshotsCollecting,
)
from source.repository_source_units_resolving import (
    RepositorySourceUnitsResolving,
)
from source.source_candidate_origin import SourceCandidateOrigin
from source.source_search_candidate import SourceSearchCandidate
from source.source_search_input import SourceSearchInput
from source.source_search_matches_resolving import SourceSearchMatchesResolving
from source.source_search_output import SourceSearchOutput
from source.source_unit_exclusion_checking import SourceUnitExclusionChecking


"""
solid-name: SourceSearchOperation
solid-category: service
solid-spec: [SPEC-040]
solid-description: Searches repository source units for exact query matches and returns bounded, deterministically ranked candidates.
"""
class SourceSearchOperation:
    def __init__(
        self,
        snapshots: RepositorySourceSnapshotsCollecting,
        units: RepositorySourceUnitsResolving,
        matches: SourceSearchMatchesResolving,
        exclusion: SourceUnitExclusionChecking,
        project_directory: Callable[[], Path],
    ) -> None:
        self._snapshots = snapshots
        self._units = units
        self._matches = matches
        self._exclusion = exclusion
        self._project_directory = project_directory

    def execute(self, operation_input: SourceSearchInput) -> SourceSearchOutput:
        root = self._project_directory().resolve()
        proposed_paths = {
            snapshot.path.resolve()
            for snapshot in operation_input.context.sources
        }
        proposed_snapshots = [
            snapshot
            for snapshot in operation_input.context.sources
            if not operation_input.included_file_extensions
            or snapshot.path.suffix.casefold()
            in operation_input.included_file_extensions
        ]
        repository_snapshots = [
            snapshot
            for snapshot in self._snapshots.collect(root)
            if snapshot.path.resolve() not in proposed_paths
            and (
                not operation_input.included_file_extensions
                or snapshot.path.suffix.casefold()
                in operation_input.included_file_extensions
            )
        ]
        candidates: list[SourceSearchCandidate] = []
        for snapshot, origin in [
            *[
                (snapshot, SourceCandidateOrigin.PROPOSED)
                for snapshot in proposed_snapshots
            ],
            *[
                (snapshot, SourceCandidateOrigin.REPOSITORY)
                for snapshot in repository_snapshots
            ],
        ]:
            for unit in self._units.resolve(snapshot):
                if self._exclusion.is_excluded(
                    root,
                    unit,
                    operation_input.excluded_units,
                ):
                    continue
                matches = self._matches.resolve(unit, operation_input.queries)
                if matches:
                    candidates.append(SourceSearchCandidate(
                        unit=unit.unit,
                        unit_identity=unit.unit_identity,
                        description=unit.description,
                        path=unit.path,
                        source_identity=unit.source_identity,
                        start_offset=unit.start_offset,
                        end_offset=unit.end_offset,
                        content_sha256=unit.content_sha256,
                        origin=origin,
                        matches=matches,
                    ))
        ordered = sorted(
            candidates,
            key=lambda candidate: (
                -len(candidate.matches),
                candidate.source_identity,
                candidate.unit,
            ),
        )
        return SourceSearchOutput(
            candidates=ordered[:operation_input.max_candidates],
            files_scanned=(
                len(proposed_snapshots)
                + len(repository_snapshots)
            ),
        )
