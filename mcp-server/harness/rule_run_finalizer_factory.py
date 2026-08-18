"""Composes deterministic executable-rule finalization dependencies."""

from harness.completed_step_outputs_resolver import CompletedStepOutputsResolver
from harness.event_appender import EventAppending
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.metric_band_matcher import MetricBandMatcher
from harness.metric_scoring_evaluator import MetricScoringEvaluator
from harness.rule_observation_collector import RuleObservationCollector
from harness.rule_result_event_publisher import RuleResultEventPublisher
from harness.rule_review_result_builder import RuleReviewResultBuilder
from harness.rule_review_result_persister import RuleReviewResultPersister
from harness.rule_run_finalizer import RuleRunFinalizer
from harness.run_completion_finalizing import RunCompletionFinalizing
from harness.worst_review_severity_selector import WorstReviewSeveritySelector


"""
solid-name: RuleRunFinalizerFactory
solid-category: factory
solid-spec: [SPEC-039]
solid-description: Composes the deterministic scoring, persistence, and audit collaborators for rule-run completion.
"""
class RuleRunFinalizerFactory:
    def build(
        self,
        event_appender: EventAppending,
    ) -> RunCompletionFinalizing:
        error_factory = FlowValidationErrorFactory()
        return RuleRunFinalizer(
            observation_collector=RuleObservationCollector(
                outputs_resolver=CompletedStepOutputsResolver(error_factory),
                error_factory=error_factory,
            ),
            result_builder=RuleReviewResultBuilder(
                scorer=MetricScoringEvaluator(MetricBandMatcher()),
                severity_selector=WorstReviewSeveritySelector(),
            ),
            result_persister=RuleReviewResultPersister(),
            event_publisher=RuleResultEventPublisher(event_appender),
        )
