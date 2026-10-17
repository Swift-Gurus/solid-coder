from pydantic import BaseModel, ConfigDict, Field

from source.source_search_context import SourceSearchContext
from source.source_search_target import SourceSearchTarget


"""
solid-name: DiscoverSourceDeclarationInput
solid-category: model
solid-spec: [SPEC-057]
solid-description: Selects a prepared declaration and authoritative source context for bounded related-declaration discovery.
"""
class DiscoverSourceDeclarationInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    target: SourceSearchTarget
    context: SourceSearchContext
    follow_related_declarations: bool = True
    max_candidates: int = Field(default=20, ge=1, le=100)
    max_bytes_per_candidate: int = Field(default=65_536, ge=1, le=1_048_576)
