"""Defines common audit identity for effective review policy state."""

from pydantic import BaseModel, ConfigDict


"""
solid-name: ReviewPolicyAudit
solid-category: model
solid-spec: [SPEC-039]
solid-description: Records the policy source classification preserved by an effective review-rule plan.
"""
class ReviewPolicyAudit(BaseModel):
    model_config = ConfigDict(frozen=True)
