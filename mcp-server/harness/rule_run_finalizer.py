"""Finalizes completed executable review-rule runs."""

from pathlib import Path

from harness.flow_def import FlowDef
from harness.rule_observation_collecting import RuleObservationCollecting
from harness.rule_result_event_publishing import RuleResultEventPublishing
from harness.rule_review_result_building import RuleReviewResultBuilding
from harness.rule_review_result_persisting import RuleReviewResultPersisting
from harness.run_completion_finalizing import RunCompletionFinalizing
from harness.run_state import RunState


"""
solid-name: RuleRunFinalizer
solid-category: service
solid-spec: [SPEC-039]
solid-description: Coordinates deterministic scoring and audit publication for a completed review-rule run.
"""
class RuleRunFinalizer(RunCompletionFinalizing):
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
        flow_def: FlowDef,
        run_state: RunState,
    ) -> None:
        if flow_def.rule is None:
            return
        observations = self._observation_collector.collect(flow_def, run_state)
        result = self._result_builder.build(
            flow_def.workflow_id,
            run_directory.name,
            observations,
        )
        self._result_persister.persist(run_directory, result)
        self._event_publisher.publish(events_path, result)
