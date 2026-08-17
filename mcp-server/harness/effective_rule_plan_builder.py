"""Coordinates deterministic effective review-rule plan construction."""

from harness.effective_rule_plan import EffectiveRulePlan
from harness.review_policy_resolution import ReviewPolicyResolution
from harness.review_policy_target_validating import ReviewPolicyTargetValidating
from harness.rule_plan_entry_building import RulePlanEntryBuilding
from harness.workflow_catalog import WorkflowCatalog


"""
solid-name: EffectiveRulePlanBuilder
solid-category: service
solid-spec: [SPEC-039]
solid-description: Coordinates validation and ordered construction of an auditable effective review-rule plan.
"""
class EffectiveRulePlanBuilder:

    def __init__(
        self,
        target_validator: ReviewPolicyTargetValidating,
        entry_builder: RulePlanEntryBuilding,
    ) -> None:
        self._target_validator = target_validator
        self._entry_builder = entry_builder

    def build(
        self,
        catalog: WorkflowCatalog,
        policy_resolution: ReviewPolicyResolution,
    ) -> EffectiveRulePlan:
        self._target_validator.validate(catalog, policy_resolution)
        return EffectiveRulePlan(
            policy=policy_resolution.audit,
            rules=[
                self._entry_builder.build(source, policy_resolution)
                for source in catalog.rule_sources()
            ],
        )
