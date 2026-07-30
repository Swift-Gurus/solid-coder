"""
solid-name: test_flow_stepper
solid-category: unit-test
solid-spec: [SPEC-013, SPEC-027]
solid-description: Tests coordinating output submission, completion checking, and delegating
execution/readiness resolution for one flow_next call.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.active_run_location import ActiveRunLocation
from harness.execution_outcome import ExecutionOutcome
from harness.flow_next_result import FlowNextResult
from harness.flow_stepper import FlowStepper
from harness.interpolation_error import InterpolationError
from harness.interpolation_guard import InterpolationGuard
from harness.models import FlowDef, RunState
from harness.run_metadata import RunMetadata
from harness.run_snapshot import RunSnapshot
from harness.step_result import StepResult
from harness.submission_outcome import SubmissionOutcome


def _location() -> ActiveRunLocation:
    return ActiveRunLocation(
        run_id="run-1", base_dir=Path("/runs"), run_dir=Path("/runs/run-1"),
        events_path="/runs/run-1/events.jsonl", workflow_path="/runs/run-1/workflow.yaml",
    )


class StubRunLocator:
    def __init__(self, location: ActiveRunLocation) -> None:
        self._location = location

    def locate(self, run_id=None) -> ActiveRunLocation:
        return self._location


class StubMetadataStore:
    def __init__(self, metadata: RunMetadata) -> None:
        self._metadata = metadata

    def write(self, run_dir: Path, metadata: RunMetadata) -> None:
        raise NotImplementedError

    def read(self, run_dir: Path) -> RunMetadata:
        return self._metadata


class StubFlowLoader:
    def __init__(self, flow_def: FlowDef) -> None:
        self._flow_def = flow_def

    def load(self, path: str, search_paths: list[str]) -> FlowDef:
        return self._flow_def


class StubRunSnapshotResolver:
    def __init__(self, snapshots: list) -> None:
        self._snapshots = list(snapshots)
        self.call_count = 0

    def resolve(self, events_path: str, flow_def: FlowDef, params: dict) -> RunSnapshot:
        outcome = self._snapshots[self.call_count]
        self.call_count += 1
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class StubSubmissionAdvancer:
    def __init__(self, outcome: SubmissionOutcome) -> None:
        self._outcome = outcome
        self.calls: list[tuple] = []

    def submit(self, events_path, base_dir, run_id, ready, step_outputs, flow_def) -> SubmissionOutcome:
        self.calls.append((events_path, base_dir, run_id, ready, step_outputs, flow_def))
        return self._outcome


class StubCompletionChecker:
    def __init__(self, result) -> None:
        self._result = result
        self.calls: list[tuple] = []

    def check(self, base_dir, run_id, events_path, flow_def, run_state):
        self.calls.append((base_dir, run_id, events_path, flow_def, run_state))
        return self._result


class StubExecutionAndReadinessCoordinator:
    def __init__(self, outcome: ExecutionOutcome | None = None) -> None:
        self._outcome = outcome or ExecutionOutcome()
        self.calls: list[tuple] = []

    def coordinate(self, effective_base_dir, run_id, events_path, flow_def, params) -> ExecutionOutcome:
        self.calls.append((effective_base_dir, run_id, events_path, flow_def, params))
        return self._outcome


class FlowStepperFactory:
    """Builds a FlowStepper with sensible stub/spy defaults; tests override only what they vary."""

    def __init__(self) -> None:
        self.run_locator = StubRunLocator(_location())
        self.metadata_store = StubMetadataStore(RunMetadata(params={}))
        self.flow_loader = StubFlowLoader(FlowDef(name="test_flow", max_turns=10, steps=[]))
        default_run_state = RunState(completed={}, running=[], turn_count=0, status="in_progress")
        self.run_snapshot_resolver = StubRunSnapshotResolver([RunSnapshot(run_state=default_run_state, ready=[])])
        self.submission_advancer = StubSubmissionAdvancer(SubmissionOutcome())
        self.completion_checker = StubCompletionChecker(None)
        self.execution_and_readiness_coordinator = StubExecutionAndReadinessCoordinator()
        self.interpolation_guard = InterpolationGuard()

    def with_flow_def(self, flow_def) -> "FlowStepperFactory":
        self.flow_loader = StubFlowLoader(flow_def)
        return self

    def with_run_snapshot_resolver(self, resolver) -> "FlowStepperFactory":
        self.run_snapshot_resolver = resolver
        return self

    def with_submission_advancer(self, advancer) -> "FlowStepperFactory":
        self.submission_advancer = advancer
        return self

    def with_completion_checker(self, checker) -> "FlowStepperFactory":
        self.completion_checker = checker
        return self

    def with_execution_and_readiness_coordinator(self, coordinator) -> "FlowStepperFactory":
        self.execution_and_readiness_coordinator = coordinator
        return self

    def make_sut(self) -> FlowStepper:
        return FlowStepper(
            run_locator=self.run_locator,
            metadata_store=self.metadata_store,
            flow_loader=self.flow_loader,
            run_snapshot_resolver=self.run_snapshot_resolver,
            submission_advancer=self.submission_advancer,
            completion_checker=self.completion_checker,
            execution_and_readiness_coordinator=self.execution_and_readiness_coordinator,
            interpolation_guard=self.interpolation_guard,
        )


class TestFlowStepper(unittest.TestCase):

    def test_returns_terminal_result_when_submission_outcome_reports_one(self):
        run_state = RunState(completed={}, running=[], turn_count=0, status="in_progress")
        terminal = FlowNextResult(status="failed")
        sut = FlowStepperFactory().with_run_snapshot_resolver(
            StubRunSnapshotResolver([RunSnapshot(run_state=run_state, ready=[])])
        ).with_submission_advancer(
            StubSubmissionAdvancer(SubmissionOutcome(terminal=terminal))
        ).make_sut()

        result = sut.flow_next({"a-1": {"bad": "value"}})

        self.assertIs(result, terminal)

    def test_returns_done_when_completion_checker_reports_done(self):
        run_state = RunState(completed={}, running=[], turn_count=0, status="in_progress")
        sut = FlowStepperFactory().with_run_snapshot_resolver(
            StubRunSnapshotResolver([RunSnapshot(run_state=run_state, ready=[])])
        ).with_submission_advancer(
            StubSubmissionAdvancer(SubmissionOutcome(run_state=run_state))
        ).with_completion_checker(
            StubCompletionChecker(FlowNextResult(status="done"))
        ).make_sut()

        result = sut.flow_next()

        self.assertEqual(result.status, "done")

    def test_returns_timed_out_when_completion_checker_reports_timed_out(self):
        run_state = RunState(completed={}, running=[], turn_count=0, status="in_progress")
        sut = FlowStepperFactory().with_flow_def(
            FlowDef(name="test_flow", max_turns=1, steps=[])
        ).with_run_snapshot_resolver(
            StubRunSnapshotResolver([RunSnapshot(run_state=run_state, ready=[])])
        ).with_submission_advancer(
            StubSubmissionAdvancer(SubmissionOutcome(run_state=run_state))
        ).with_completion_checker(
            StubCompletionChecker(FlowNextResult(status="timed_out"))
        ).make_sut()

        result = sut.flow_next()

        self.assertEqual(result.status, "timed_out")

    def test_skips_completion_check_when_nothing_was_recorded(self):
        checker_calls = StubCompletionChecker(None)
        factory = FlowStepperFactory().with_completion_checker(checker_calls)

        factory.make_sut().flow_next()

        self.assertEqual(checker_calls.calls, [])

    def test_returns_terminal_result_from_execution_and_readiness_coordinator(self):
        run_state = RunState(completed={}, running=[], turn_count=0, status="in_progress")
        terminal = FlowNextResult(status="failed")
        sut = FlowStepperFactory().with_run_snapshot_resolver(
            StubRunSnapshotResolver([RunSnapshot(run_state=run_state, ready=[])])
        ).with_submission_advancer(
            StubSubmissionAdvancer(SubmissionOutcome(run_state=run_state))
        ).with_execution_and_readiness_coordinator(
            StubExecutionAndReadinessCoordinator(ExecutionOutcome(terminal=terminal))
        ).make_sut()

        result = sut.flow_next()

        self.assertIs(result, terminal)

    def test_returns_next_ready_steps_when_run_continues(self):
        run_state = RunState(completed={}, running=[], turn_count=0, status="in_progress")
        step_result = StepResult(step_id="step-b", instance_id="step-b-1", prompt="Do step-b", execution={"mode": "inline"})
        sut = FlowStepperFactory().with_run_snapshot_resolver(
            StubRunSnapshotResolver([RunSnapshot(run_state=run_state, ready=[])])
        ).with_submission_advancer(
            StubSubmissionAdvancer(SubmissionOutcome(run_state=run_state))
        ).with_execution_and_readiness_coordinator(
            StubExecutionAndReadinessCoordinator(ExecutionOutcome(steps=[step_result]))
        ).make_sut()

        result = sut.flow_next({"step-a-1": {}})

        self.assertEqual(result.status, "ready")
        self.assertEqual(result.steps, [step_result])

    def test_calls_execution_and_readiness_coordinator_with_the_located_run_and_flow_def(self):
        flow_def = FlowDef(name="test_flow", max_turns=10, steps=[])
        run_state = RunState(completed={}, running=[], turn_count=0, status="in_progress")
        coordinator = StubExecutionAndReadinessCoordinator()
        sut = FlowStepperFactory().with_flow_def(flow_def).with_run_snapshot_resolver(
            StubRunSnapshotResolver([RunSnapshot(run_state=run_state, ready=[])])
        ).with_submission_advancer(
            StubSubmissionAdvancer(SubmissionOutcome(run_state=run_state))
        ).with_execution_and_readiness_coordinator(coordinator).make_sut()

        sut.flow_next({"step-a-1": {}})

        self.assertEqual(coordinator.calls, [
            (Path("/runs"), "run-1", "/runs/run-1/events.jsonl", flow_def, {}),
        ])

    def test_submits_the_resolved_ready_snapshot_and_outputs(self):
        flow_def = FlowDef(name="test_flow", max_turns=10, steps=[])
        run_state = RunState(completed={}, running=[], turn_count=0, status="in_progress")
        snapshot = RunSnapshot(run_state=run_state, ready=[])
        advancer = StubSubmissionAdvancer(SubmissionOutcome())
        sut = FlowStepperFactory().with_flow_def(flow_def).with_run_snapshot_resolver(
            StubRunSnapshotResolver([snapshot])
        ).with_submission_advancer(advancer).make_sut()

        sut.flow_next({"step-a-1": {"result": "ok"}})

        self.assertEqual(advancer.calls, [
            ("/runs/run-1/events.jsonl", Path("/runs"), "run-1", [], {"step-a-1": {"result": "ok"}}, flow_def),
        ])

    def test_returns_clean_error_when_initial_snapshot_interpolation_fails(self):
        sut = FlowStepperFactory().with_run_snapshot_resolver(
            StubRunSnapshotResolver([InterpolationError("bad reference")])
        ).make_sut()

        result = sut.flow_next()

        self.assertEqual(result.status, "ready")
        self.assertEqual(result.error, "bad reference")

    def test_returns_clean_error_when_execution_and_readiness_coordinator_reports_an_error(self):
        sut = FlowStepperFactory().with_execution_and_readiness_coordinator(
            StubExecutionAndReadinessCoordinator(ExecutionOutcome(error="bad reference"))
        ).make_sut()

        result = sut.flow_next()

        self.assertEqual(result.status, "ready")
        self.assertEqual(result.error, "bad reference")


if __name__ == "__main__":
    unittest.main()
