"""Defines authoritative prospective sources available during repository comparison."""

from pydantic import BaseModel, ConfigDict, Field

from source.repository_source_snapshot import RepositorySourceSnapshot


"""
solid-name: SourceSearchContext
solid-category: model
solid-spec: [SPEC-040, SPEC-041]
solid-description: Carries authoritative prospective source snapshots through deterministic search and candidate resolution.
"""
class SourceSearchContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sources: list[RepositorySourceSnapshot] = Field(default_factory=list)
