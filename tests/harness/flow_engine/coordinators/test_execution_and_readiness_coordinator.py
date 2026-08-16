"""
solid-name: test_execution_and_readiness_coordinator
solid-category: unit-test
solid-spec: [SPEC-031, SPEC-027, SPEC-035]
solid-description: Tests automatic execution, completion detection, and external readiness coordination.
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
from harness.models import FlowDef, RunState
from harness.run_snapshot import RunSnapshot
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


class StubStepResultBuilder:
    def __init__(self, steps: list[StepResult] | None = None, error: InterpolationError | None = None) -> None:
        self._steps = steps or []
        self._error = error
        self.calls: list[tuple] = []

    def build(self, instances, flow_def, run_state) -> list[StepResult]:
        self.calls.append((instances, flow_def, run_state))
        if self._error is not None:
            raise self._error
        return self._steps


class StubRunSnapshotResolver:
    def __init__(self, snapshot: RunSnapshot) -> None:
        self.snapshot = snapshot

    def resolve(self, events_path, flow_def, params) -> RunSnapshot:
        return self.snapshot


class StubCompletionChecker:
    def __init__(self, result: FlowNextResult | None = None) -> None:
        self.result = result
        self.run_state = None

    def check(self, base_dir, run_id, events_path, flow_def, run_state):
        self.run_state = run_state
        return self.result


class ExecutionAndReadinessCoordinatorFactory:
    def __init__(self) -> None:
        self.step_execution_coordinator = StubStepExecutionCoordinator(None)
        self.step_result_builder = StubStepResultBuilder([])
        self.interpolation_guard = InterpolationGuard()
        run_state = RunState(completed={}, running=[], turn_count=0, status="in_progress")
        flow_def = FlowDef(name="flow", max_turns=10, steps=[])
        self.run_snapshot_resolver = StubRunSnapshotResolver(
            RunSnapshot(run_state=run_state, flow_def=flow_def, ready=[])
        )
        self.completion_checker = StubCompletionChecker()

    def with_step_execution_coordinator(self, coordinator) -> "ExecutionAndReadinessCoordinatorFactory":
        self.step_execution_coordinator = coordinator
        return self

    def with_step_result_builder(self, builder) -> "ExecutionAndReadinessCoordinatorFactory":
        self.step_result_builder = builder
        return self

    def with_completion_checker(self, checker) -> "ExecutionAndReadinessCoordinatorFactory":
        self.completion_checker = checker
        return self

    def make_sut(self) -> ExecutionAndReadinessCoordinator:
        return ExecutionAndReadinessCoordinator(
            step_execution_coordinator=self.step_execution_coordinator,
            step_result_builder=self.step_result_builder,
            interpolation_guard=self.interpolation_guard,
            run_snapshot_resolver=self.run_snapshot_resolver,
            completion_checker=self.completion_checker,
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

    def test_does_not_build_step_results_when_a_terminal_result_is_reported(self):
        step_result_builder = StubStepResultBuilder([])
        sut = ExecutionAndReadinessCoordinatorFactory().with_step_execution_coordinator(
            StubStepExecutionCoordinator(FlowNextResult(status="failed"))
        ).with_step_result_builder(step_result_builder).make_sut()

        sut.coordinate(Path("/runs"), "run-1", "/runs/run-1/events.jsonl", _FLOW_DEF, {})

        self.assertEqual(step_result_builder.calls, [])

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
        sut = ExecutionAndReadinessCoordinatorFactory().with_step_result_builder(
            StubStepResultBuilder([step])
        ).make_sut()

        result = sut.coordinate(Path("/runs"), "run-1", "/runs/run-1/events.jsonl", _FLOW_DEF, {})

        self.assertEqual(result.steps, [step])
        self.assertIsNone(result.terminal)
        self.assertIsNone(result.error)

    def test_returns_terminal_completion_before_resolving_external_steps(self):
        terminal = FlowNextResult(status="done")
        step_result_builder = StubStepResultBuilder([])
        checker = StubCompletionChecker(terminal)
        sut = ExecutionAndReadinessCoordinatorFactory().with_completion_checker(
            checker
        ).with_step_result_builder(step_result_builder).make_sut()

        result = sut.coordinate(Path("/runs"), "run-1", "/runs/run-1/events.jsonl", _FLOW_DEF, {})

        self.assertIs(result.terminal, terminal)
        self.assertEqual(step_result_builder.calls, [])
        self.assertIsNotNone(checker.run_state)

    def test_returns_an_error_when_step_result_builder_raises_interpolation_error(self):
        sut = ExecutionAndReadinessCoordinatorFactory().with_step_result_builder(
            StubStepResultBuilder(error=InterpolationError("bad reference"))
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

    def test_passes_the_resolved_snapshot_to_the_step_result_builder(self):
        step_result_builder = StubStepResultBuilder([])
        factory = ExecutionAndReadinessCoordinatorFactory().with_step_result_builder(step_result_builder)
        snapshot = factory.run_snapshot_resolver.snapshot
        sut = factory.make_sut()

        sut.coordinate(Path("/runs"), "run-1", "/runs/run-1/events.jsonl", _FLOW_DEF, {"key": "value"})

        self.assertEqual(step_result_builder.calls, [
            (snapshot.ready, snapshot.flow_def, snapshot.run_state),
        ])


if __name__ == "__main__":
    unittest.main()
