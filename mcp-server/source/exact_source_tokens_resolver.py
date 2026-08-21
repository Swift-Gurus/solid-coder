"""Resolves normalized exact-match tokens from source text."""

from source.source_tokens_resolving import SourceTokensResolving


"""
solid-name: ExactSourceTokensResolver
solid-category: service
solid-spec: [SPEC-040]
solid-description: Produces case-normalized identifier and word tokens from source text without pattern expressions.
"""
class ExactSourceTokensResolver(SourceTokensResolving):
    def resolve(self, content: str) -> set[str]:
        normalized = "".join(
            character if character.isalnum() or character == "_" else " "
            for character in content.casefold()
        )
        return set(normalized.split())
