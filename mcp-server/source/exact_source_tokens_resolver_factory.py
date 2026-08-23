"""Composes the shared exact source-token resolver."""

from source.camel_case_identifier_segmenter import CamelCaseIdentifierSegmenter
from source.exact_source_tokens_resolver import ExactSourceTokensResolver


"""
solid-name: ExactSourceTokensResolverFactory
solid-category: factory
solid-spec: [SPEC-040]
solid-description: Constructs a ready-to-use exact source-token resolver for shared search.
"""
class ExactSourceTokensResolverFactory:
    def make(self) -> ExactSourceTokensResolver:
        return ExactSourceTokensResolver(
            identifier_segmenter=CamelCaseIdentifierSegmenter()
        )
