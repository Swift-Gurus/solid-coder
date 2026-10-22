"""Defines one record in the flat JSON submission boundary."""

from pydantic import BaseModel, ConfigDict, Field, JsonValue


"""
solid-name: FlatSubmissionRecord
solid-category: model
solid-spec: [SPEC-068]
solid-description: Carries a strict assignment address and its opaque authored named-output JSON for existing schema validation.
"""
class FlatSubmissionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    id: str = Field(min_length=1)
    result: dict[str, JsonValue]
