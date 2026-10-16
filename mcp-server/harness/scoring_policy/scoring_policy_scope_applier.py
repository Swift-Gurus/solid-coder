from dataclasses import replace

from harness.effective_metric_plan_resolving import EffectiveMetricPlanResolving
from harness.effective_metric_scoring_applier import EffectiveMetricScoringApplying
from harness.flow_def import FlowDef
from harness.review_policy_resolution import ReviewPolicyResolution
from harness.scoring_policy.metric_plan_applying import MetricPlanApplying
from harness.step_def import StepDef


"""
solid-name: ScoringPolicyScopeApplier
solid-category: service
solid-spec: [SPEC-039, SPEC-057]
solid-description: Resolves one rule scope's effective metric plans and applies them through a shared typed step transformation contract.
"""
class ScoringPolicyScopeApplier(EffectiveMetricScoringApplying):
    def __init__(self, plan_resolver: EffectiveMetricPlanResolving, step_applier: MetricPlanApplying[StepDef]) -> None:
        self._plan_resolver = plan_resolver
        self._step_applier = step_applier

    def apply(self, flow: FlowDef, policy: ReviewPolicyResolution) -> FlowDef:
        plans = self._plan_resolver.resolve(flow, policy)
        return replace(flow, steps=[self._step_applier.apply(step, plans) for step in flow.steps])
