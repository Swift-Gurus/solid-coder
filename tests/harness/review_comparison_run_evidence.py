"""Defines durable evidence for one legacy or workflow review comparison run."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from review_comparison_stage_evidence import ReviewComparisonStageEvidence


"""
solid-name: ReviewComparisonRunEvidence
solid-category: test-support
solid-spec: [SPEC-036, SPEC-041]
solid-description: Records identity, accuracy inputs, performance, usage, and completion evidence for one comparable review run.
"""
class ReviewComparisonRunEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    approach: Literal["legacy-health", "workflow-review"]
    phase: Literal["smoke", "measurement"]
    iteration: int = Field(ge=0)
    model_profile: str = Field(min_length=1)
    model: str = Field(min_length=1)
    target_path: str = Field(min_length=1)
    target_sha256: str = Field(min_length=64, max_length=64)
    effective_instructions_sha256: str = Field(min_length=64, max_length=64)
    active_rule_ids: list[str] = Field(min_length=1)
    review_stage: ReviewComparisonStageEvidence
    full_run: ReviewComparisonStageEvidence
    reported_cost_available: bool
    reported_cost_usd: float = Field(ge=0)
    retry_count: int = Field(ge=0)
    error_count: int = Field(ge=0)
    completed: bool
