"""Coordinates validated DRY searches for health checks."""

from health.dry_search_completion_recording import DrySearchCompletionRecording
from health.dry_search_coordinating import DrySearchCoordinating
from search.search_terms_resolving import SearchTermsResolving
from search.tag_codebase_searching import TagCodebaseSearching

"""
solid-name: DrySearchCoordinator
solid-category: coordinator
solid-description: Coordinates validated codebase search and successful DRY-search completion recording.
"""


class DrySearchCoordinator(DrySearchCoordinating):
    def __init__(
        self,
        search: TagCodebaseSearching,
        terms: SearchTermsResolving,
        completion: DrySearchCompletionRecording,
    ) -> None:
        self._search = search
        self._terms = terms
        self._completion = completion

    def search(
        self,
        sources_dir: str | None = None,
        plan_path: str | None = None,
        query: str | None = None,
        tags: list[str] | None = None,
        spec_numbers: list[str] | None = None,
        min_matches: int = 1,
        output_dir: str | None = None,
    ) -> str:
        try:
            resolved_terms = self._terms.resolve(query, tags)
        except ValueError as error:
            return f"Error: {error}"

        result = self._search.search(
            sources_dir=sources_dir,
            plan_path=plan_path,
            tags=resolved_terms,
            spec_numbers=spec_numbers,
            min_matches=min_matches,
        )
        if output_dir and not result.startswith("Error:"):
            self._completion.record(output_dir)
        return result
