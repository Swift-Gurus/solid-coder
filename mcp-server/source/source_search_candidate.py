"""Defines one typed repository source-search candidate."""

from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from source.source_search_match import SourceSearchMatch
from source.source_candidate_origin import SourceCandidateOrigin

SourceIdentity = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]
ContentSha256 = Annotated[
    str,
    StringConstraints(pattern=r"^[0-9a-f]{64}$"),
]


"""
solid-name: SourceSearchCandidate
solid-category: model
solid-spec: [SPEC-040]
solid-description: Represents one bounded repository unit selected by source search.
"""
class SourceSearchCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    unit: str = Field(min_length=1)
    unit_identity: str = Field(min_length=1)
    description: str = Field(min_length=1)
    path: Path
    source_identity: SourceIdentity
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)
    content_sha256: ContentSha256
    origin: SourceCandidateOrigin
    matches: Annotated[list[SourceSearchMatch], Field(min_length=1)]
