"""Finalizes all completed rule instances in one review-capable workflow run."""

from pathlib import Path

from harness.flow_def import FlowDef
from harness.review_result_building import ReviewResultBuilding
from harness.review_result_persisting import ReviewResultPersisting
from harness.rule_execution_finalizing import RuleExecutionFinalizing
from harness.rule_execution_instances_resolving import (
    RuleExecutionInstancesResolving,
)
from harness.run_completion_finalizing import RunCompletionFinalizing
from harness.run_state import RunState


"""
solid-name: ReviewRunFinalizer
solid-category: service
solid-spec: [SPEC-039]
solid-description: Finalizes completed rule instances and publishes one ordered aggregate result for a workflow run.
"""
class ReviewRunFinalizer(RunCompletionFinalizing):
    def __init__(
        self,
        instances_resolver: RuleExecutionInstancesResolving,
        rule_finalizer: RuleExecutionFinalizing,
        result_builder: ReviewResultBuilding,
        result_persister: ReviewResultPersisting,
    ) -> None:
        self._instances_resolver = instances_resolver
        self._rule_finalizer = rule_finalizer
        self._result_builder = result_builder
        self._result_persister = result_persister

    def finalize(
        self,
        run_directory: Path,
        events_path: str,
        flow_def: FlowDef,
        run_state: RunState,
    ) -> None:
        instances = self._instances_resolver.resolve(
            flow_def,
            run_state,
            run_directory.name,
        )
        if not instances:
            return
        results = [
            self._rule_finalizer.finalize(
                run_directory,
                events_path,
                instance,
                run_state,
            )
            for instance in instances
        ]
        self._result_persister.persist(
            run_directory,
            self._result_builder.build(flow_def.workflow_id, results),
        )
