"""Coordinates automatic execution, completion, and external readiness."""

from __future__ import annotations

from pathlib import Path

from harness.execution_and_readiness_coordinating import ExecutionAndReadinessCoordinating
from harness.execution_outcome import ExecutionOutcome
from harness.interpolation_guarding import InterpolationGuarding
from harness.models import FlowDef
from harness.ready_steps_resolving import ReadyStepsResolving
from harness.run_completion_checking import RunCompletionChecking
from harness.run_snapshot_resolving import RunSnapshotResolving
from harness.step_execution_coordinating import StepExecutionCoordinating


"""
solid-name: ExecutionAndReadinessCoordinator
solid-category: service
solid-spec: [SPEC-031, SPEC-035]
solid-description: Coordinates automatic workflow execution, terminal completion, and externally ready steps.
"""
class ExecutionAndReadinessCoordinator(ExecutionAndReadinessCoordinating):

    def __init__(
        self,
        step_execution_coordinator: StepExecutionCoordinating,
        ready_steps_resolver: ReadyStepsResolving,
        interpolation_guard: InterpolationGuarding,
        run_snapshot_resolver: RunSnapshotResolving,
        completion_checker: RunCompletionChecking,
    ) -> None:
        self._step_execution_coordinator = step_execution_coordinator
        self._ready_steps_resolver = ready_steps_resolver
        self._interpolation_guard = interpolation_guard
        self._run_snapshot_resolver = run_snapshot_resolver
        self._completion_checker = completion_checker

    def coordinate(
        self,
        effective_base_dir: Path,
        run_id: str,
        events_path: str,
        flow_def: FlowDef,
        params: dict,
    ) -> ExecutionOutcome:
        terminal, error = self._interpolation_guard.guard(
            lambda: self._step_execution_coordinator.run_ready(effective_base_dir, run_id, events_path, flow_def, params)
        )
        if error is not None:
            return ExecutionOutcome(error=error)
        if terminal is not None:
            return ExecutionOutcome(terminal=terminal)

        snapshot, error = self._interpolation_guard.guard(
            lambda: self._run_snapshot_resolver.resolve(events_path, flow_def, params)
        )
        if error is not None:
            return ExecutionOutcome(error=error)
        terminal = self._completion_checker.check(
            effective_base_dir,
            run_id,
            events_path,
            flow_def,
            snapshot.run_state,
        )
        if terminal is not None:
            return ExecutionOutcome(terminal=terminal)

        steps, error = self._interpolation_guard.guard(
            lambda: self._ready_steps_resolver.resolve(events_path, flow_def, params)
        )
        if error is not None:
            return ExecutionOutcome(error=error)
        return ExecutionOutcome(steps=steps)
