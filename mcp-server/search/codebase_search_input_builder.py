"""Builds typed source-search input from codebase-search boundary arguments."""

from collections.abc import Callable
from pathlib import Path

from source.repository_target_resolver import RepositoryTargetResolving
from source.source_search_input import SourceSearchInput
from source.source_search_query import SourceSearchQuery

from search.codebase_search_input_building import CodebaseSearchInputBuilding
from search.codebase_search_input_resolution import CodebaseSearchInputResolution
from search.codebase_search_query_kind import CodebaseSearchQueryKind
from search.codebase_search_terms_resolving import CodebaseSearchTermsResolving

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
        query_kinds: type[CodebaseSearchQueryKind],
        targets: RepositoryTargetResolving,
    ) -> None:
        self._current_directory = current_directory
        self._terms = terms
        self._query_kinds = query_kinds
        self._targets = targets

    def build(
        self,
        sources_dir: str | None,
        plan_path: str | None,
        tags: list[str] | None,
        spec_numbers: list[str] | None,
        min_matches: int,
    ) -> CodebaseSearchInputResolution:
        project_root = self._targets.resolve(
            self._current_directory(), Path(sources_dir) if sources_dir else Path(".")
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
            queries.append(
                SourceSearchQuery(
                    id=self._query_kinds.TERMS.value,
                    terms=resolved_terms.terms,
                )
            )
        if resolved_terms.specifications:
            queries.append(
                SourceSearchQuery(
                    id=self._query_kinds.SPECIFICATIONS.value,
                    terms=resolved_terms.specifications,
                )
            )
        if not queries:
            raise ValueError("provide plan_path, tags, or spec_numbers to search.")
        return CodebaseSearchInputResolution(
            operation_input=SourceSearchInput(
                queries=queries,
                max_candidates=100,
            ),
            project_root=project_root.resolve(),
            minimum_matches=min_matches,
        )
