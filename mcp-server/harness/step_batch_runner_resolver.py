"""Selects batch execution for a workflow step's type and mode."""

from __future__ import annotations

from harness.models import StepDef
from harness.step_batch_running import StepBatchRunning
from harness.step_batch_runner_registration import StepBatchRunnerRegistration
from harness.step_batch_runner_resolving import StepBatchRunnerResolving


"""
solid-name: StepBatchRunnerResolver
solid-category: service
solid-spec: [SPEC-037]
solid-description: Resolves the batch execution capability registered for a workflow step type and mode.
"""
class StepBatchRunnerResolver(StepBatchRunnerResolving):
    def __init__(self, registrations: list[StepBatchRunnerRegistration]) -> None:
        self._registrations = registrations

    def resolve(self, step_def: StepDef) -> StepBatchRunning:
        for registration in self._registrations:
            if registration.matches(step_def):
                return registration.runner
        raise ValueError(
            f"No batch runner registered for step type '{step_def.type}' "
            f"and mode '{step_def.mode}'"
        )
