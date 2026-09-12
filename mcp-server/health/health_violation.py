"""Defines one severe source-health violation."""

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: HealthViolation
solid-category: model
solid-spec: [SPEC-036, SPEC-039]
solid-description: Represents a severe review finding with its diagnostic context.
"""
class HealthViolation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    principle: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    issue: str = Field(min_length=1)
    evidence: str = Field(min_length=1)
    fix: str = ""
