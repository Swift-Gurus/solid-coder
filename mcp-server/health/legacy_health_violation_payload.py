"""Validates one finding emitted by the unchanged legacy extractor."""

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: LegacyHealthViolationPayload
solid-category: model
solid-spec: [SPEC-050]
solid-description: Represents one validated finding emitted by legacy health review extraction.
"""
class LegacyHealthViolationPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    principle: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    issue: str = Field(min_length=1)
    fix: str = ""
