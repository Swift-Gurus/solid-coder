"""Coordinates typed repository source search."""

from source.repository_source_snapshots_collecting import (
    RepositorySourceSnapshotsCollecting,
)
from source.repository_source_units_resolving import (
    RepositorySourceUnitsResolving,
)
from source.source_search_candidate import SourceSearchCandidate
from source.source_search_input import SourceSearchInput
from source.source_search_matches_resolving import SourceSearchMatchesResolving
from source.source_search_output import SourceSearchOutput


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
    ) -> None:
        self._snapshots = snapshots
        self._units = units
        self._matches = matches

    def execute(self, operation_input: SourceSearchInput) -> SourceSearchOutput:
        snapshots = self._snapshots.collect(operation_input.project_root)
        excluded = set(operation_input.excluded_source_identities)
        candidates: list[SourceSearchCandidate] = []
        for snapshot in snapshots:
            if (
                snapshot.source_identity in excluded
                or str(snapshot.path) in excluded
            ):
                continue
            for unit in self._units.resolve(snapshot):
                matches = self._matches.resolve(unit, operation_input.queries)
                if matches:
                    candidates.append(SourceSearchCandidate(
                        unit=unit.unit,
                        description=unit.description,
                        path=unit.path,
                        source_identity=unit.source_identity,
                        content_sha256=unit.content_sha256,
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
            files_scanned=len(snapshots),
        )
