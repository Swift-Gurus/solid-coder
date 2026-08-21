"""Applies codebase-search eligibility policy to typed source candidates."""

from search.codebase_search_query_kind import CodebaseSearchQueryKind
from search.source_search_output_filtering import SourceSearchOutputFiltering
from source.source_search_output import SourceSearchOutput


"""
solid-name: SourceSearchOutputFilter
solid-category: service
solid-spec: [SPEC-040]
solid-description: Retains source candidates that satisfy term thresholds or match requested specifications.
"""
class SourceSearchOutputFilter(SourceSearchOutputFiltering):
    def filter(
        self,
        output: SourceSearchOutput,
        minimum_matches: int,
    ) -> SourceSearchOutput:
        if minimum_matches < 1:
            raise ValueError("min_matches must be at least 1.")
        return SourceSearchOutput(
            candidates=[
                candidate
                for candidate in output.candidates
                if len(candidate.matches) >= minimum_matches
                or any(
                    match.query_id
                    == CodebaseSearchQueryKind.SPECIFICATIONS.value
                    for match in candidate.matches
                )
            ],
            files_scanned=output.files_scanned,
        )
