"""Defines construction of one effective rule-plan entry."""

from typing import Protocol

from harness.effective_rule_plan_entry import EffectiveRulePlanEntry
from harness.review_policy_resolution import ReviewPolicyResolution
from harness.workflow_source import WorkflowSource


"""
solid-name: RulePlanEntryBuilding
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for constructing auditable effective-plan entries from enrolled workflow sources.
"""
class RulePlanEntryBuilding(Protocol):
    def build(
        self,
        source: WorkflowSource,
        policy_resolution: ReviewPolicyResolution,
    ) -> EffectiveRulePlanEntry: ...
