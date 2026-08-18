"""Coordinates deterministic effective review-rule plan construction."""

from harness.effective_rule_plan import EffectiveRulePlan
from harness.flow_loading import FlowLoading
from harness.ordered_string_collecting import OrderedStringCollecting
from harness.resolved_rule_workflow import ResolvedRuleWorkflow
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
        flow_loader: FlowLoading,
        search_path_collector: OrderedStringCollecting,
    ) -> None:
        self._target_validator = target_validator
        self._entry_builder = entry_builder
        self._flow_loader = flow_loader
        self._search_path_collector = search_path_collector

    def build(
        self,
        catalog: WorkflowCatalog,
        policy_resolution: ReviewPolicyResolution,
    ) -> EffectiveRulePlan:
        self._target_validator.validate(catalog, policy_resolution)
        search_paths = self._search_path_collector.collect(
            [
                [str(source.package_root or source.entry_path.parent)]
                for source in catalog.sources
            ]
        )
        resolved_rules = [
            ResolvedRuleWorkflow(
                source=source,
                workflow=self._flow_loader.load(
                    str(source.entry_path),
                    search_paths,
                ),
            )
            for source in catalog.rule_sources()
        ]
        return EffectiveRulePlan(
            policy=policy_resolution.audit,
            rules=[
                self._entry_builder.build(resolved_rule, policy_resolution)
                for resolved_rule in resolved_rules
            ],
        )
