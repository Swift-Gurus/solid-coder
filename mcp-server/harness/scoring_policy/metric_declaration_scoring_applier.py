from harness.effective_metric_plan_entry import EffectiveMetricPlanEntry
from harness.metric_declaration import MetricDeclaration
from harness.scoring_policy.metric_plan_applying import MetricPlanApplying

"""
solid-name: MetricDeclarationScoringApplier
solid-category: service
solid-spec: [SPEC-039, SPEC-057]
solid-description: Replaces a metric's severity bands from its resolved policy plan without discarding measurement or evidence-availability metadata.
"""


class MetricDeclarationScoringApplier(MetricPlanApplying[MetricDeclaration]):
    def apply(
        self, value: MetricDeclaration, plans: list[EffectiveMetricPlanEntry]
    ) -> MetricDeclaration:
        plan = next(
            entry
            for entry in plans
            if entry.metric_id == value.metric_id
            and entry.observation_id == value.observation_id
        )
        return MetricDeclaration(
            metric_id=value.metric_id,
            observation_id=value.observation_id,
            value=value.value,
            scoring=plan.effective_scoring,
            unavailable_reason=value.unavailable_reason,
        )
