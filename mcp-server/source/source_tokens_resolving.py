"""Defines normalized token extraction from source text."""

from typing import Protocol


"""
solid-name: SourceTokensResolving
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for resolving normalized exact-match tokens from source text.
"""
class SourceTokensResolving(Protocol):
    def resolve(self, content: str) -> set[str]: ...
