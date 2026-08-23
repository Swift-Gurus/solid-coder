"""Defines timing and token evidence for one comparison stage."""

from pydantic import BaseModel, ConfigDict, Field

from codex_token_usage import CodexTokenUsage


"""
solid-name: ReviewComparisonStageEvidence
solid-category: test-support
solid-spec: [SPEC-036, SPEC-041]
solid-description: Carries elapsed time and cumulative token usage observed at one review comparison boundary.
"""
class ReviewComparisonStageEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    elapsed_seconds: float = Field(ge=0)
    token_usage: CodexTokenUsage
