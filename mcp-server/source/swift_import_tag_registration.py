"""Defines tags emitted for one exact Swift import."""

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: SwiftImportTagRegistration
solid-category: model
solid-spec: [SPEC-040]
solid-description: Associates one exact Swift module import with ordered normalized source tags.
"""
class SwiftImportTagRegistration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    module: str = Field(min_length=1)
    tags: list[str] = Field(min_length=1)
