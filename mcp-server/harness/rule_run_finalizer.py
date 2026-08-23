"""Finalizes completed executable review-rule runs."""

from pathlib import Path

from harness.rule_execution_finalizing import RuleExecutionFinalizing
from harness.rule_execution_instance import RuleExecutionInstance
from harness.rule_observation_collecting import RuleObservationCollecting
from harness.rule_result_event_publishing import RuleResultEventPublishing
from harness.rule_review_result import RuleReviewResult
from harness.rule_review_result_building import RuleReviewResultBuilding
from harness.rule_review_result_persisting import RuleReviewResultPersisting
from harness.run_state import RunState


"""
solid-name: RuleRunFinalizer
solid-category: service
solid-spec: [SPEC-039]
solid-description: Produces and publishes the deterministic scored result for one completed rule execution instance.
"""
class RuleRunFinalizer(RuleExecutionFinalizing):
    def __init__(
        self,
        observation_collector: RuleObservationCollecting,
        result_builder: RuleReviewResultBuilding,
        result_persister: RuleReviewResultPersisting,
        event_publisher: RuleResultEventPublishing,
    ) -> None:
        self._observation_collector = observation_collector
        self._result_builder = result_builder
        self._result_persister = result_persister
        self._event_publisher = event_publisher

    def finalize(
        self,
        run_directory: Path,
        events_path: str,
        instance: RuleExecutionInstance,
        run_state: RunState,
    ) -> RuleReviewResult:
        observations = self._observation_collector.collect(instance, run_state)
        result = self._result_builder.build(
            instance.workflow.workflow_id,
            instance.instance_id,
            instance.provenance,
            observations,
        )
        self._result_persister.persist(run_directory, result)
        self._event_publisher.publish(events_path, result)
        return result
