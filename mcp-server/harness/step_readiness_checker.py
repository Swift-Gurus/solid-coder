"""Coordinates workflow-step readiness checks."""

from __future__ import annotations

from harness.models import RunState, StepDef
from harness.step_dependency_checking import StepDependencyChecking
from harness.step_readiness_checking import StepReadinessChecking
from harness.step_status_checking import StepStatusChecking


"""
solid-name: StepReadinessChecker
solid-category: service
solid-spec: [SPEC-010, SPEC-030]
solid-description: Coordinates workflow step status and dependency readiness through focused collaborators.
"""
class StepReadinessChecker(StepReadinessChecking):
    def __init__(
        self,
        status_checker: StepStatusChecking,
        dependency_checker: StepDependencyChecking,
    ) -> None:
        self._status_checker = status_checker
        self._dependency_checker = dependency_checker

    def is_done_or_running(self, step_id: str, run_state: RunState) -> bool:
        return self._status_checker.is_done_or_running(step_id, run_state)

    def dependencies_met(self, step: StepDef, run_state: RunState) -> bool:
        return self._dependency_checker.dependencies_met(step, run_state)
