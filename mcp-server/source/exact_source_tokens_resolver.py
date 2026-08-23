"""Resolves normalized exact-match tokens from source text."""

from source.identifier_segmenting import IdentifierSegmenting
from source.source_tokens_resolving import SourceTokensResolving


"""
solid-name: ExactSourceTokensResolver
solid-category: service
solid-spec: [SPEC-040]
solid-description: Resolves normalized source-text and identifier-component tokens for exact matching.
"""
class ExactSourceTokensResolver(SourceTokensResolving):
    def __init__(self, identifier_segmenter: IdentifierSegmenting) -> None:
        self._identifier_segmenter = identifier_segmenter

    def resolve(self, content: str) -> set[str]:
        words = "".join(
            character if character.isalnum() or character == "_" else " "
            for character in content
        )
        tokens: set[str] = set()
        for word in words.split():
            tokens.add(word.casefold())
            for underscore_component in word.split("_"):
                if not underscore_component:
                    continue
                tokens.add(underscore_component.casefold())
                tokens.update(
                    component.casefold()
                    for component in self._identifier_segmenter.segment(
                        underscore_component
                    )
                )
        return tokens
