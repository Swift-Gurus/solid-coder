"""Builds deterministic results from validated executable-rule observations."""

from findings.review_severity import ReviewSeverity
from harness.metric_scoring_evaluating import MetricScoringEvaluating
from harness.review_severity_selecting import ReviewSeveritySelecting
from harness.rule_metric_decision import RuleMetricDecision
from harness.rule_observations import RuleObservations
from harness.rule_review_provenance import RuleReviewProvenance
from harness.rule_review_result import RuleReviewResult
from harness.rule_review_result_building import RuleReviewResultBuilding

"""
solid-name: RuleReviewResultBuilder
solid-category: service
solid-spec: [SPEC-039]
solid-description: Builds authoritative metric and aggregate severity decisions for one review rule.
"""


class RuleReviewResultBuilder(RuleReviewResultBuilding):
    def __init__(
        self,
        scorer: MetricScoringEvaluating,
        severity_selector: ReviewSeveritySelecting,
    ) -> None:
        self._scorer = scorer
        self._severity_selector = severity_selector

    def build(
        self,
        workflow_id: str,
        rule_instance_id: str,
        provenance: RuleReviewProvenance,
        observations: RuleObservations,
    ) -> RuleReviewResult:
        decisions: list[RuleMetricDecision] = []
        for observation in observations.metrics:
            raw_severity = self._scorer.evaluate(
                observation.value,
                observation.declaration.scoring,
            )
            matching_band = None
            if raw_severity is ReviewSeverity.SEVERE:
                matching_band = observation.declaration.scoring.severe
            elif raw_severity is ReviewSeverity.MINOR:
                matching_band = observation.declaration.scoring.minor
            decisions.append(
                RuleMetricDecision(
                    metric_id=observation.declaration.metric_id,
                    observation_id=observation.declaration.observation_id,
                    value=observation.value,
                    severity=(
                        ReviewSeverity.COMPLIANT
                        if observations.exception.is_exception
                        else raw_severity
                    ),
                    additional_info=observation.additional_info,
                    derivation=observation.derivation,
                    raw_severity=(
                        raw_severity if observation.derivation is not None else None
                    ),
                    matching_band=(
                        matching_band if observation.derivation is not None else None
                    ),
                )
            )
        return RuleReviewResult(
            workflow_id=workflow_id,
            rule_instance_id=rule_instance_id,
            provenance=provenance,
            severity=self._severity_selector.select(decisions) if decisions else None,
            exception=observations.exception,
            metrics=decisions,
            unavailable_metrics=observations.unavailable_metrics,
        )
