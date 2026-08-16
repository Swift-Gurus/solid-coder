"""Coordinates bounded concurrent execution of session-delegate instances."""

from __future__ import annotations

from harness.concurrent_item_mapping import ConcurrentItemMapping
from harness.models import StepInstance
from harness.session_delegate_batch_running import SessionDelegateBatchRunning
from harness.session_delegate_instance_running import SessionDelegateInstanceRunning
from harness.step_instance_execution import StepInstanceExecution


"""
solid-name: ConcurrentSessionDelegateBatchRunner
solid-category: service
solid-spec: [SPEC-037]
solid-description: Coordinates bounded concurrent session-delegate execution while preserving source order.
"""
class ConcurrentSessionDelegateBatchRunner(SessionDelegateBatchRunning):
    def __init__(
        self,
        item_mapper: ConcurrentItemMapping,
        instance_runner: SessionDelegateInstanceRunning,
        max_workers: int,
    ) -> None:
        self._item_mapper = item_mapper
        self._instance_runner = instance_runner
        self._max_workers = max_workers

    def run(
        self,
        instances: list[StepInstance],
    ) -> list[StepInstanceExecution]:
        return self._item_mapper.map(
            self._instance_runner.run,
            instances,
            self._max_workers,
        )
