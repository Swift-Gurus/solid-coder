"""Carries a host transcript content block."""

from pydantic import BaseModel, ConfigDict


"""
solid-name: TranscriptContentBlock
solid-category: model
solid-description: Carries the kind and optional text of a transcript content block.
"""
class TranscriptContentBlock(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    type: str = ""
    text: str | None = None
