"""Constructs one effective rule-plan entry from an enrolled workflow."""

from harness.content_hashing import ContentHashing
from harness.effective_rule_plan_entry import EffectiveRulePlanEntry
from harness.effective_metric_plan_resolving import EffectiveMetricPlanResolving
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.review_policy_resolution import ReviewPolicyResolution
from harness.resolved_rule_workflow import ResolvedRuleWorkflow
from harness.rule_enablement_resolving import RuleEnablementResolving
from harness.rule_plan_entry_building import RulePlanEntryBuilding
from harness.rule_workflow_origin_resolving import RuleWorkflowOriginResolving


"""
solid-name: RulePlanEntryBuilder
solid-category: service
solid-spec: [SPEC-039]
solid-description: Constructs one auditable effective-plan entry from workflow provenance, enablement, and effective metrics.
"""
class RulePlanEntryBuilder(RulePlanEntryBuilding):

    def __init__(
        self,
        content_hasher: ContentHashing,
        enablement_resolver: RuleEnablementResolving,
        origin_resolver: RuleWorkflowOriginResolving,
        metric_plan_resolver: EffectiveMetricPlanResolving,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._content_hasher = content_hasher
        self._enablement_resolver = enablement_resolver
        self._origin_resolver = origin_resolver
        self._metric_plan_resolver = metric_plan_resolver
        self._error_factory = error_factory

    def build(
        self,
        resolved_rule: ResolvedRuleWorkflow,
        policy_resolution: ReviewPolicyResolution,
    ) -> EffectiveRulePlanEntry:
        source = resolved_rule.source
        if source.rule is None:
            raise self._error_factory.create(
                f"Workflow '{source.id}' is not enrolled as a review rule"
            )
        try:
            workflow_content = source.entry_path.read_bytes()
        except OSError as error:
            raise self._error_factory.create(
                f"Rule workflow '{source.entry_path}' could not be hashed: {error}"
            ) from error
        return EffectiveRulePlanEntry(
            workflow_id=source.id,
            origin=self._origin_resolver.resolve(source),
            source_path=source.entry_path.resolve(),
            workflow_hash=self._content_hasher.hash(workflow_content),
            category=source.rule.category or "",
            required_tags=source.rule.tags,
            enablement=self._enablement_resolver.resolve(
                source.id,
                policy_resolution,
            ),
            metrics=self._metric_plan_resolver.resolve(
                resolved_rule.workflow,
                policy_resolution,
            ),
        )
