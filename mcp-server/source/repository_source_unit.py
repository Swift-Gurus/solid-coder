"""Defines one searchable unit within a repository source snapshot."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from source.source_frontmatter import SourceFrontmatter


"""
solid-name: RepositorySourceUnit
solid-category: model
solid-spec: [SPEC-040]
solid-description: Carries one searchable source unit, its LLM-facing summary, and immutable file identity.
"""
class RepositorySourceUnit(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    unit: str = Field(min_length=1)
    description: str = Field(min_length=1)
    path: Path
    source_identity: str = Field(min_length=1)
    frontmatter: SourceFrontmatter
    file_content: str
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
