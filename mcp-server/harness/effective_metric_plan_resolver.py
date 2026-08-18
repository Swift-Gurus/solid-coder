"""Resolves workflow metric defaults and project policy overrides."""

from harness.effective_metric_plan_entry import EffectiveMetricPlanEntry
from harness.effective_metric_plan_resolving import EffectiveMetricPlanResolving
from harness.flow_def import FlowDef
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.metric_override_applying import MetricOverrideApplying
from harness.review_policy_resolution import ReviewPolicyResolution


"""
solid-name: EffectiveMetricPlanResolver
solid-category: service
solid-spec: [SPEC-039]
solid-description: Validates metric override coordinates and coordinates effective metric planning for one rule workflow.
"""
class EffectiveMetricPlanResolver(EffectiveMetricPlanResolving):
    def __init__(
        self,
        override_applier: MetricOverrideApplying,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._override_applier = override_applier
        self._error_factory = error_factory

    def resolve(
        self,
        workflow: FlowDef,
        policy_resolution: ReviewPolicyResolution,
    ) -> list[EffectiveMetricPlanEntry]:
        rule_override = next(
            (
                override
                for override in policy_resolution.policy.rules
                if override.workflow_id == workflow.workflow_id
            ),
            None,
        )
        metric_overrides = rule_override.metrics if rule_override is not None else []
        declared_metrics = [
            step.metric for step in workflow.steps if step.metric is not None
        ]
        declared_ids = {metric.metric_id for metric in declared_metrics}
        for override in metric_overrides:
            if override.id not in declared_ids:
                raise self._error_factory.create(
                    f"Review policy targets unknown metric '{override.id}' in rule workflow '{workflow.workflow_id}'"
                )

        effective_metrics = [
            self._override_applier.apply(
                metric,
                next(
                    (
                        override
                        for override in metric_overrides
                        if override.id == metric.metric_id
                    ),
                    None,
                ),
                policy_resolution,
            )
            for metric in declared_metrics
        ]
        if not any(metric.effective_enabled for metric in effective_metrics):
            raise self._error_factory.create(
                f"Rule workflow '{workflow.workflow_id}' must retain at least one enabled metric"
            )
        return effective_metrics
