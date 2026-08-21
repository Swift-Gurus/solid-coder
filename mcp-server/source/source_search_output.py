"""Defines typed repository source-search output."""

from pydantic import BaseModel, ConfigDict

from source.source_search_candidate import SourceSearchCandidate


"""
solid-name: SourceSearchOutput
solid-category: model
solid-spec: [SPEC-040]
solid-description: Returns stable typed search candidates and the auditable scan count.
"""
class SourceSearchOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidates: list[SourceSearchCandidate]
    files_scanned: int
