"""Defines the immutable rule plan snapshotted before review execution."""

from typing import Literal, Union

from pydantic import BaseModel, ConfigDict, Field

from harness.default_review_policy_audit import DefaultReviewPolicyAudit
from harness.effective_rule_plan_entry import EffectiveRulePlanEntry
from harness.project_review_policy_audit import ProjectReviewPolicyAudit


"""
solid-name: EffectiveRulePlan
solid-category: model
solid-spec: [SPEC-039]
solid-description: Records ordered executable review rules and their effective project-policy audit source.
"""
class EffectiveRulePlan(BaseModel):
    model_config = ConfigDict(frozen=True)

    version: Literal[1] = 1
    policy: Union[DefaultReviewPolicyAudit, ProjectReviewPolicyAudit]
    rules: list[EffectiveRulePlanEntry] = Field(default_factory=list)
