"""Prepares one deterministic source-search query."""

from gate.file_extension_extracting import FileExtensionExtracting
from source.prepare_search_query_input import PrepareSearchQueryInput
from source.prepare_search_query_output import PrepareSearchQueryOutput
from source.source_search_query import SourceSearchQuery
from source.source_tokens_resolving import SourceTokensResolving
from source.source_unit_identity import SourceUnitIdentity


"""
solid-name: PrepareSearchQueryOperation
solid-category: service
solid-spec: [SPEC-040]
solid-description: Normalizes and combines deterministic and runtime terms into one target-owned source-search query.
"""
class PrepareSearchQueryOperation:
    def __init__(
        self,
        tokens: SourceTokensResolving,
        extension: FileExtensionExtracting,
    ) -> None:
        self._tokens = tokens
        self._extension = extension

    def execute(
        self,
        operation_input: PrepareSearchQueryInput,
    ) -> PrepareSearchQueryOutput:
        terms: list[str] = []
        for term in [
            *operation_input.target.deterministic_terms,
            *operation_input.generated_terms,
        ]:
            for normalized in [
                term.casefold(),
                *sorted(self._tokens.resolve(term)),
            ]:
                if normalized not in terms:
                    terms.append(normalized)
        return PrepareSearchQueryOutput(
            queries=[SourceSearchQuery(
                id=operation_input.target.identity,
                terms=terms,
            )],
            excluded_units=[SourceUnitIdentity(
                source_identity=operation_input.target.source_identity,
                unit_identity=operation_input.target.unit_identity,
            )],
            included_file_extensions=[
                self._extension.suffix_of(
                    operation_input.target.source_identity
                )
            ],
        )
