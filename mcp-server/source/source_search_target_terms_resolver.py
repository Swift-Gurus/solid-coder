"""Resolves deterministic terms for one prepared source-search target."""

from harness.ordered_string_collecting import OrderedStringCollecting
from source.source_tokens_resolving import SourceTokensResolving


"""
solid-name: SourceSearchTargetTermsResolver
solid-category: service
solid-spec: [SPEC-040]
solid-description: Combines normalized target-name tokens and MCP-detected tags in stable order.
"""
class SourceSearchTargetTermsResolver:
    def __init__(
        self,
        tokens: SourceTokensResolving,
        strings: OrderedStringCollecting,
    ) -> None:
        self._tokens = tokens
        self._strings = strings

    def resolve(self, name: str, detected_tags: list[str]) -> list[str]:
        return self._strings.collect([
            sorted(self._tokens.resolve(name)),
            [tag.casefold() for tag in detected_tags],
        ])
