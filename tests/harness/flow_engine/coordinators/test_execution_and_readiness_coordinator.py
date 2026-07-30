"""
solid-name: test_execution_and_readiness_coordinator
solid-category: unit-test
solid-spec: [SPEC-013, SPEC-027]
solid-description: Tests running a flow's ready steps to completion or halt, then resolving its readiness.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.execution_and_readiness_coordinator import ExecutionAndReadinessCoordinator
from harness.flow_next_result import FlowNextResult
from harness.interpolation_error import InterpolationError
from harness.interpolation_guard import InterpolationGuard
from harness.models import FlowDef
from harness.step_result import StepResult


class StubStepExecutionCoordinator:
    def __init__(self, result: FlowNextResult | None = None, error: InterpolationError | None = None) -> None:
        self._result = result
        self._error = error
        self.calls: list[tuple] = []

    def run_ready(self, base_dir, run_id, events_path, flow_def, params):
        self.calls.append((base_dir, run_id, events_path, flow_def, params))
        if self._error is not None:
            raise self._error
        return self._result


class StubReadyStepsResolver:
    def __init__(self, steps: list[StepResult] | None = None, error: InterpolationError | None = None) -> None:
        self._steps = steps or []
        self._error = error
        self.calls: list[tuple] = []

    def resolve(self, events_path, flow_def, params) -> list[StepResult]:
        self.calls.append((events_path, flow_def, params))
        if self._error is not None:
            raise self._error
        return self._steps


class ExecutionAndReadinessCoordinatorFactory:
    def __init__(self) -> None:
        self.step_execution_coordinator = StubStepExecutionCoordinator(None)
        self.ready_steps_resolver = StubReadyStepsResolver([])
        self.interpolation_guard = InterpolationGuard()

    def with_step_execution_coordinator(self, coordinator) -> "ExecutionAndReadinessCoordinatorFactory":
        self.step_execution_coordinator = coordinator
        return self

    def with_ready_steps_resolver(self, resolver) -> "ExecutionAndReadinessCoordinatorFactory":
        self.ready_steps_resolver = resolver
        return self

    def make_sut(self) -> ExecutionAndReadinessCoordinator:
        return ExecutionAndReadinessCoordinator(
            step_execution_coordinator=self.step_execution_coordinator,
            ready_steps_resolver=self.ready_steps_resolver,
            interpolation_guard=self.interpolation_guard,
        )


_FLOW_DEF = FlowDef(name="code_review", max_turns=10, steps=[])


class TestExecutionAndReadinessCoordinator(unittest.TestCase):

    def test_returns_the_terminal_result_when_step_execution_coordinator_reports_one(self):
        terminal = FlowNextResult(status="failed", error="Flow failed — step 'doomed' exhausted all 2 attempt(s).")
        sut = ExecutionAndReadinessCoordinatorFactory().with_step_execution_coordinator(
            StubStepExecutionCoordinator(terminal)
        ).make_sut()

        result = sut.coordinate(Path("/runs"), "run-1", "/runs/run-1/events.jsonl", _FLOW_DEF, {})

        self.assertIs(result.terminal, terminal)
        self.assertEqual(result.steps, [])
        self.assertIsNone(result.error)

    def test_does_not_resolve_readiness_when_a_terminal_result_is_reported(self):
        ready_steps_resolver = StubReadyStepsResolver([])
        sut = ExecutionAndReadinessCoordinatorFactory().with_step_execution_coordinator(
            StubStepExecutionCoordinator(FlowNextResult(status="failed"))
        ).with_ready_steps_resolver(ready_steps_resolver).make_sut()

        sut.coordinate(Path("/runs"), "run-1", "/runs/run-1/events.jsonl", _FLOW_DEF, {})

        self.assertEqual(ready_steps_resolver.calls, [])

    def test_returns_an_error_when_step_execution_coordinator_raises_interpolation_error(self):
        sut = ExecutionAndReadinessCoordinatorFactory().with_step_execution_coordinator(
            StubStepExecutionCoordinator(error=InterpolationError("bad reference"))
        ).make_sut()

        result = sut.coordinate(Path("/runs"), "run-1", "/runs/run-1/events.jsonl", _FLOW_DEF, {})

        self.assertEqual(result.error, "bad reference")
        self.assertIsNone(result.terminal)
        self.assertEqual(result.steps, [])

    def test_returns_the_resolved_steps_when_no_terminal_result(self):
        step = StepResult(step_id="a", instance_id="a-1", prompt="Do a", execution={"mode": "inline"})
        sut = ExecutionAndReadinessCoordinatorFactory().with_ready_steps_resolver(
            StubReadyStepsResolver([step])
        ).make_sut()

        result = sut.coordinate(Path("/runs"), "run-1", "/runs/run-1/events.jsonl", _FLOW_DEF, {})

        self.assertEqual(result.steps, [step])
        self.assertIsNone(result.terminal)
        self.assertIsNone(result.error)

    def test_returns_an_error_when_ready_steps_resolver_raises_interpolation_error(self):
        sut = ExecutionAndReadinessCoordinatorFactory().with_ready_steps_resolver(
            StubReadyStepsResolver(error=InterpolationError("bad reference"))
        ).make_sut()

        result = sut.coordinate(Path("/runs"), "run-1", "/runs/run-1/events.jsonl", _FLOW_DEF, {})

        self.assertEqual(result.error, "bad reference")

    def test_passes_the_given_arguments_through_to_the_step_execution_coordinator(self):
        step_execution_coordinator = StubStepExecutionCoordinator(None)
        sut = ExecutionAndReadinessCoordinatorFactory().with_step_execution_coordinator(
            step_execution_coordinator
        ).make_sut()

        sut.coordinate(Path("/runs"), "run-1", "/runs/run-1/events.jsonl", _FLOW_DEF, {"key": "value"})

        self.assertEqual(step_execution_coordinator.calls, [
            (Path("/runs"), "run-1", "/runs/run-1/events.jsonl", _FLOW_DEF, {"key": "value"}),
        ])

    def test_passes_events_path_flow_def_and_params_through_to_the_ready_steps_resolver(self):
        ready_steps_resolver = StubReadyStepsResolver([])
        sut = ExecutionAndReadinessCoordinatorFactory().with_ready_steps_resolver(ready_steps_resolver).make_sut()

        sut.coordinate(Path("/runs"), "run-1", "/runs/run-1/events.jsonl", _FLOW_DEF, {"key": "value"})

        self.assertEqual(ready_steps_resolver.calls, [
            ("/runs/run-1/events.jsonl", _FLOW_DEF, {"key": "value"}),
        ])


if __name__ == "__main__":
    unittest.main()
