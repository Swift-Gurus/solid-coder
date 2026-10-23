from dataclasses import replace

from harness.effective_metric_plan_entry import EffectiveMetricPlanEntry
from harness.metric_declaration import MetricDeclaration
from harness.rule_assessment_declaration import RuleAssessmentDeclaration
from harness.scoring_policy.metric_plan_applying import MetricPlanApplying
from harness.step_def import StepDef

"""
solid-name: StepScoringApplier
solid-category: service
solid-spec: [SPEC-039, SPEC-057]
solid-description: Applies policy plans to ordinary and assessment metric declarations while preserving executable step metadata.
"""


class StepScoringApplier(MetricPlanApplying[StepDef]):
    def __init__(self, metric_applier: MetricPlanApplying[MetricDeclaration]) -> None:
        self._metric_applier = metric_applier

    def apply(self, value: StepDef, plans: list[EffectiveMetricPlanEntry]) -> StepDef:
        metric = (
            self._metric_applier.apply(value.metric, plans)
            if value.metric is not None
            else None
        )
        assessment = value.assessment
        if assessment is not None:
            assessment = RuleAssessmentDeclaration(
                supporting_outputs=assessment.supporting_outputs,
                metrics=[
                    self._metric_applier.apply(declaration, plans)
                    for declaration in assessment.metrics
                ],
                exception_observation_id=assessment.exception_observation_id,
            )
        return replace(value, metric=metric, assessment=assessment)
