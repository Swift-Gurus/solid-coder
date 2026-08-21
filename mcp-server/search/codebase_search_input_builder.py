"""Builds typed source-search input from codebase-search boundary arguments."""

from pathlib import Path
from typing import Callable, Optional

from search.codebase_search_input_building import CodebaseSearchInputBuilding
from search.codebase_search_input_resolution import CodebaseSearchInputResolution
from search.codebase_search_query_kind import CodebaseSearchQueryKind
from search.codebase_search_terms_resolving import CodebaseSearchTermsResolving
from source.source_search_input import SourceSearchInput
from source.source_search_query import SourceSearchQuery

"""
solid-name: CodebaseSearchInputBuilder
solid-category: service
solid-spec: [SPEC-040]
solid-description: Translates codebase-search arguments into validated source-search input.
"""
class CodebaseSearchInputBuilder(CodebaseSearchInputBuilding):

    def __init__(
        self,
        current_directory: Callable[[], Path],
        terms: CodebaseSearchTermsResolving,
    ) -> None:
        self._current_directory = current_directory
        self._terms = terms

    def build(
        self,
        sources_dir: Optional[str],
        plan_path: Optional[str],
        tags: Optional[list[str]],
        spec_numbers: Optional[list[str]],
        min_matches: int,
    ) -> CodebaseSearchInputResolution:
        project_root = (
            Path(sources_dir) if sources_dir else self._current_directory()
        )
        if not project_root.is_dir():
            raise ValueError(f"sources_dir not found: {project_root}")
        resolved_terms = self._terms.resolve(
            Path(plan_path) if plan_path else None,
            tags,
            spec_numbers,
        )

        queries: list[SourceSearchQuery] = []
        if resolved_terms.terms:
            queries.append(SourceSearchQuery(
                id=CodebaseSearchQueryKind.TERMS.value,
                terms=resolved_terms.terms,
            ))
        if resolved_terms.specifications:
            queries.append(SourceSearchQuery(
                id=CodebaseSearchQueryKind.SPECIFICATIONS.value,
                terms=resolved_terms.specifications,
            ))
        if not queries:
            raise ValueError("provide plan_path, tags, or spec_numbers to search.")
        return CodebaseSearchInputResolution(
            operation_input=SourceSearchInput(
                project_root=project_root,
                queries=queries,
                max_candidates=100,
            ),
            minimum_matches=min_matches,
        )
