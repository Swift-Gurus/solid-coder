"""Defines construction of an effective review-rule plan."""

from typing import Protocol

from harness.effective_rule_plan import EffectiveRulePlan
from harness.review_policy_resolution import ReviewPolicyResolution
from harness.workflow_catalog import WorkflowCatalog


"""
solid-name: EffectiveRulePlanBuilding
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for constructing an ordered effective rule plan from catalog and policy state.
"""
class EffectiveRulePlanBuilding(Protocol):
    def build(
        self,
        catalog: WorkflowCatalog,
        policy_resolution: ReviewPolicyResolution,
    ) -> EffectiveRulePlan: ...
