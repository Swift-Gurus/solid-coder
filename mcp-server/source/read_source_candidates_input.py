"""Defines typed input for bounded candidate-source loading."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from source.source_search_candidate import SourceSearchCandidate


"""
solid-name: ReadSourceCandidatesInput
solid-category: model
solid-spec: [SPEC-040]
solid-description: Selects typed search candidates and the per-candidate content bound used for audit and replay.
"""
class ReadSourceCandidatesInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    project_root: Path
    candidates: list[SourceSearchCandidate]
    max_bytes_per_candidate: int = Field(default=65_536, ge=1, le=1_048_576)
