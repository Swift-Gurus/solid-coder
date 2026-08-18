"""Defines project-policy application to one declared review metric."""

from typing import Optional, Protocol

from harness.effective_metric_plan_entry import EffectiveMetricPlanEntry
from harness.metric_declaration import MetricDeclaration
from harness.review_policy_metric_override import ReviewPolicyMetricOverride
from harness.review_policy_resolution import ReviewPolicyResolution


"""
solid-name: MetricOverrideApplying
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for applying one optional project policy override to one authored metric declaration.
"""
class MetricOverrideApplying(Protocol):
    def apply(
        self,
        metric: MetricDeclaration,
        override: Optional[ReviewPolicyMetricOverride],
        policy_resolution: ReviewPolicyResolution,
    ) -> EffectiveMetricPlanEntry: ...
