"""Defines construction of one effective rule-plan entry."""

from typing import Protocol

from harness.effective_rule_plan_entry import EffectiveRulePlanEntry
from harness.resolved_rule_workflow import ResolvedRuleWorkflow
from harness.review_policy_resolution import ReviewPolicyResolution


"""
solid-name: RulePlanEntryBuilding
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for constructing auditable effective-plan entries from resolved enrolled rule workflows.
"""
class RulePlanEntryBuilding(Protocol):
    def build(
        self,
        resolved_rule: ResolvedRuleWorkflow,
        policy_resolution: ReviewPolicyResolution,
    ) -> EffectiveRulePlanEntry: ...
