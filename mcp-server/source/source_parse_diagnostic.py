"""Defines a recoverable deterministic source parse diagnostic."""

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: SourceParseDiagnostic
solid-category: model
solid-spec: [SPEC-040]
solid-description: Records a recoverable source parse issue with stable code and line evidence.
"""
class SourceParseDiagnostic(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    line: int = Field(ge=1)
