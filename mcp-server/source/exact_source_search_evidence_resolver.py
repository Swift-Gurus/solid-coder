"""Prepares lexical search evidence independently of query terms."""

from typing import Protocol

from source.repository_source_unit import RepositorySourceUnit
from source.source_search_evidence import SourceSearchEvidence
from source.source_tokens_resolving import SourceTokensResolving


"""
solid-name: SourceSearchEvidenceResolving
solid-category: abstraction
solid-spec: [SPEC-060]
solid-description: Contract for preparing reusable lexical evidence for source-unit search.
"""
class SourceSearchEvidenceResolving(Protocol):
    def resolve(self, unit: RepositorySourceUnit) -> SourceSearchEvidence: ...


"""
solid-name: ExactSourceSearchEvidenceResolver
solid-category: service
solid-spec: [SPEC-060]
solid-description: Prepares normalized lexical evidence for source search without repeating extraction for each query term.
"""
class ExactSourceSearchEvidenceResolver(SourceSearchEvidenceResolving):
    def __init__(self, tokens: SourceTokensResolving) -> None:
        self._tokens = tokens

    def resolve(self, unit: RepositorySourceUnit) -> SourceSearchEvidence:
        imports = frozenset(
            line.strip().split()[1].split(".")[0].casefold()
            for line in unit.file_content.splitlines()
            if line.strip().startswith("import ")
            and len(line.strip().split()) > 1
        )
        values = [
            unit.frontmatter.name,
            unit.frontmatter.category,
            *unit.frontmatter.tags,
            *unit.frontmatter.stack,
            *unit.frontmatter.specs,
        ]
        frontmatter = {value.casefold() for value in values if value}
        frontmatter.update(self._tokens.resolve("\n".join([
            *values, unit.frontmatter.description,
        ])))
        content = "" if unit.frontmatter.name else unit.content
        return SourceSearchEvidence(
            filename=unit.path.name.casefold(),
            imports=imports,
            frontmatter=frozenset(frontmatter),
            symbols=frozenset(self._tokens.resolve(content)) if content else frozenset(),
            content=content.casefold(),
        )
