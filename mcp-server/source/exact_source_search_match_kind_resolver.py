"""Classifies exact source evidence for repository search terms."""

from __future__ import annotations

from source.repository_source_unit import RepositorySourceUnit
from source.source_search_match_kind import SourceSearchMatchKind
from source.source_search_match_kind_resolving import (
    SourceSearchMatchKindResolving,
)
from source.source_tokens_resolving import SourceTokensResolving


"""
solid-name: ExactSourceSearchMatchKindResolver
solid-category: service
solid-spec: [SPEC-040]
solid-description: Classifies exact filename, import, frontmatter, symbol, and content matches from source snapshots.
"""
class ExactSourceSearchMatchKindResolver(SourceSearchMatchKindResolving):
    def __init__(self, tokens: SourceTokensResolving) -> None:
        self._tokens = tokens

    def resolve(
        self,
        unit: RepositorySourceUnit,
        normalized_term: str,
    ) -> SourceSearchMatchKind | None:
        if normalized_term in unit.path.name.casefold():
            return SourceSearchMatchKind.FILENAME
        lines = unit.file_content.splitlines()
        imports = [
            line.strip().split()[1].split(".")[0].casefold()
            for line in lines
            if line.strip().startswith("import ")
            and len(line.strip().split()) > 1
        ]
        if normalized_term in imports:
            return SourceSearchMatchKind.IMPORT
        exact_frontmatter_values = {
            value.casefold()
            for value in [
                unit.frontmatter.name,
                unit.frontmatter.category,
                *unit.frontmatter.tags,
                *unit.frontmatter.stack,
                *unit.frontmatter.specs,
            ]
            if value
        }
        if normalized_term in exact_frontmatter_values:
            return SourceSearchMatchKind.FRONTMATTER
        frontmatter_text = "\n".join([
            unit.frontmatter.name,
            unit.frontmatter.description,
            unit.frontmatter.category,
            *unit.frontmatter.tags,
            *unit.frontmatter.stack,
            *unit.frontmatter.specs,
        ])
        if normalized_term in self._tokens.resolve(frontmatter_text):
            return SourceSearchMatchKind.FRONTMATTER
        if unit.frontmatter.name:
            return None
        if normalized_term in self._tokens.resolve(unit.content):
            return SourceSearchMatchKind.SYMBOL
        if normalized_term in unit.content.casefold():
            return SourceSearchMatchKind.CONTENT
        return None
