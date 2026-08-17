"""Defines the singular typed client review policy document."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from harness.review_policy_rule_override import ReviewPolicyRuleOverride


"""
solid-name: ReviewPolicy
solid-category: model
solid-spec: [SPEC-039]
solid-description: Represents versioned client overrides for executable review-rule workflows.
"""
class ReviewPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: Literal[1]
    rules: list[ReviewPolicyRuleOverride] = Field(default_factory=list)
