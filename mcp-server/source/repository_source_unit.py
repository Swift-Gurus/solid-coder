"""Defines one searchable unit within a repository source snapshot."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from source.source_frontmatter import SourceFrontmatter


"""
solid-name: RepositorySourceUnit
solid-category: model
solid-spec: [SPEC-040]
solid-description: Represents one searchable unit resolved from repository source.
"""
class RepositorySourceUnit(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    unit: str = Field(min_length=1)
    unit_identity: str = Field(min_length=1)
    description: str = Field(min_length=1)
    path: Path
    source_identity: str = Field(min_length=1)
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)
    content: str
    frontmatter: SourceFrontmatter
    file_content: str
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
