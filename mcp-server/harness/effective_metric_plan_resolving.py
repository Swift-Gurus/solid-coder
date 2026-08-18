"""Defines effective metric planning for one resolved review rule."""

from typing import Protocol

from harness.effective_metric_plan_entry import EffectiveMetricPlanEntry
from harness.flow_def import FlowDef
from harness.review_policy_resolution import ReviewPolicyResolution


"""
solid-name: EffectiveMetricPlanResolving
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for resolving workflow metric defaults and project overrides into effective metric plans.
"""
class EffectiveMetricPlanResolving(Protocol):
    def resolve(
        self,
        workflow: FlowDef,
        policy_resolution: ReviewPolicyResolution,
    ) -> list[EffectiveMetricPlanEntry]: ...
