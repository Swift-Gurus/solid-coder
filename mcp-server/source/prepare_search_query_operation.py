"""Prepares one deterministic source-search query."""

from source.prepare_search_query_input import PrepareSearchQueryInput
from source.prepare_search_query_output import PrepareSearchQueryOutput
from source.source_search_query import SourceSearchQuery


"""
solid-name: PrepareSearchQueryOperation
solid-category: service
solid-spec: [SPEC-040]
solid-description: Normalizes and combines deterministic and runtime terms into one target-owned source-search query.
"""
class PrepareSearchQueryOperation:
    def execute(
        self,
        operation_input: PrepareSearchQueryInput,
    ) -> PrepareSearchQueryOutput:
        terms: list[str] = []
        for term in [
            *operation_input.target.deterministic_terms,
            *operation_input.generated_terms,
        ]:
            normalized = term.casefold()
            if normalized not in terms:
                terms.append(normalized)
        exclusions: list[str] = []
        for identity in operation_input.excluded_source_identities:
            if identity not in exclusions:
                exclusions.append(identity)
        return PrepareSearchQueryOutput(
            queries=[SourceSearchQuery(
                id=operation_input.target.identity,
                terms=terms,
            )],
            excluded_source_identities=exclusions,
        )
