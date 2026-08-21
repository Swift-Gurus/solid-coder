"""Defines an immutable readable repository source snapshot."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict


"""
solid-name: RepositorySourceSnapshot
solid-category: model
solid-spec: [SPEC-040]
solid-description: Carries canonical repository source identity, exact text, and content hash captured by one search.
"""
class RepositorySourceSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: Path
    source_identity: str
    content: str
    content_sha256: str
