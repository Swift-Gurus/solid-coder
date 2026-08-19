"""Defines auditable evidence for one deterministic source detection."""

from pydantic import BaseModel, ConfigDict, Field

from source.source_line_range import SourceLineRange


"""
solid-name: SourceEvidence
solid-category: model
solid-spec: [SPEC-040]
solid-description: Records one parsed source fact and its inclusive line span as detection evidence.
"""
class SourceEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    fact: str = Field(min_length=1)
    span: SourceLineRange
