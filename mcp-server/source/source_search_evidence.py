"""Carries normalized lexical evidence for one source-search unit."""

from pydantic import BaseModel, ConfigDict


"""
solid-name: SourceSearchEvidence
solid-category: model
solid-spec: [SPEC-060]
solid-description: Represents normalized lexical evidence for repeatable source-unit search across multiple queries.
"""
class SourceSearchEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    filename: str
    imports: frozenset[str]
    frontmatter: frozenset[str]
    symbols: frozenset[str]
    content: str
