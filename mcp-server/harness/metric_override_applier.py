"""Applies one optional project override to one authored review metric."""

from typing import Optional, cast

from harness.effective_metric_plan_entry import EffectiveMetricPlanEntry
from harness.metric_declaration import MetricDeclaration
from harness.metric_override_applying import MetricOverrideApplying
from harness.metric_policy_override_audit import MetricPolicyOverrideAudit
from harness.project_review_policy_audit import ProjectReviewPolicyAudit
from harness.review_policy_metric_override import ReviewPolicyMetricOverride
from harness.review_policy_resolution import ReviewPolicyResolution


"""
solid-name: MetricOverrideApplier
solid-category: service
solid-spec: [SPEC-039]
solid-description: Applies project enablement and scoring values over one metric while preserving audit provenance.
"""
class MetricOverrideApplier(MetricOverrideApplying):
    def apply(
        self,
        metric: MetricDeclaration,
        override: Optional[ReviewPolicyMetricOverride],
        policy_resolution: ReviewPolicyResolution,
    ) -> EffectiveMetricPlanEntry:
        if override is None:
            return EffectiveMetricPlanEntry(
                metric_id=metric.metric_id,
                observation_id=metric.observation_id,
                effective_enabled=True,
                authored_scoring=metric.scoring,
                effective_scoring=metric.scoring,
            )
        return EffectiveMetricPlanEntry(
            metric_id=metric.metric_id,
            observation_id=metric.observation_id,
            effective_enabled=(
                override.enabled if override.enabled is not None else True
            ),
            authored_scoring=metric.scoring,
            effective_scoring=override.scoring or metric.scoring,
            policy_override=MetricPolicyOverrideAudit(
                requested_enabled=override.enabled,
                requested_scoring=override.scoring,
                policy=cast(ProjectReviewPolicyAudit, policy_resolution.audit),
                reason=override.reason,
            ),
        )
