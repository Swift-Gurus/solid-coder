"""
solid-name: test_flow_stepper
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests coordinating output validation, recording, turn advancement, and completion for one flow_next call.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.active_run_location import ActiveRunLocation
from harness.flow_next_result import FlowNextResult
from harness.flow_stepper import FlowStepper
from harness.interpolation_error import InterpolationError
from harness.models import FlowDef, RunState, StepInstance
from harness.run_metadata import RunMetadata
from harness.run_snapshot import RunSnapshot
from harness.step_result import StepResult


def _location() -> ActiveRunLocation:
    return ActiveRunLocation(
        run_id="run-1", base_dir=Path("/runs"), run_dir=Path("/runs/run-1"),
        events_path="/runs/run-1/events.jsonl", workflow_path="/runs/run-1/workflow.yaml",
    )


class StubRunLocator:
    def __init__(self, location: ActiveRunLocation) -> None:
        self._location = location

    def locate(self) -> ActiveRunLocation:
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


class StubOutputValidator:
    def __init__(self, errors: list[str]) -> None:
        self._errors = errors

    def validate(self, ready: list, outputs: dict, flow_def: FlowDef) -> list[str]:
        return self._errors


class StubSessionReader:
    def read_session_id(self) -> str:
        return "session-42"


class SpyOutputRecorder:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def record(self, events_path: str, ready: list, step_outputs: dict, session_id: str) -> None:
        self.calls.append((events_path, ready, step_outputs, session_id))


class StubTurnAdvancer:
    def __init__(self, run_state: RunState) -> None:
        self._run_state = run_state
        self.calls: list[str] = []

    def advance(self, events_path: str) -> RunState:
        self.calls.append(events_path)
        return self._run_state


class StubCompletionChecker:
    def __init__(self, result) -> None:
        self._result = result
        self.calls: list[tuple] = []

    def check(self, base_dir, run_id, events_path, flow_def, run_state):
        self.calls.append((base_dir, run_id, events_path, flow_def, run_state))
        return self._result


class StubStepResultBuilder:
    def __init__(self, steps: list[StepResult]) -> None:
        self._steps = steps

    def build(self, instances, flow_def, detected_env) -> list[StepResult]:
        return self._steps


def _make_stepper(
    flow_def, snapshots, validation_errors=None, run_state_after_advance=None,
    completion_result=None, next_steps=None, metadata=None,
):
    return FlowStepper(
        run_locator=StubRunLocator(_location()),
        metadata_store=StubMetadataStore(metadata or RunMetadata(params={}, detected_env="")),
        flow_loader=StubFlowLoader(flow_def),
        run_snapshot_resolver=StubRunSnapshotResolver(snapshots),
        output_validator=StubOutputValidator(validation_errors or []),
        session_reader=StubSessionReader(),
        output_recorder=SpyOutputRecorder(),
        turn_advancer=StubTurnAdvancer(run_state_after_advance or RunState(completed={}, running=[], turn_count=1, status="in_progress")),
        completion_checker=StubCompletionChecker(completion_result),
        step_result_builder=StubStepResultBuilder(next_steps or []),
    )


class TestFlowStepper(unittest.TestCase):

    def test_returns_validation_error_without_recording_or_advancing(self):
        flow_def = FlowDef(name="test_flow", max_turns=10, steps=[])
        run_state = RunState(completed={}, running=[], turn_count=0, status="in_progress")
        sut = _make_stepper(flow_def, snapshots=[RunSnapshot(run_state=run_state, ready=[])],
                             validation_errors=["output.name is required"])

        result = sut.flow_next({"step-a-1": {"bad": "value"}})

        self.assertEqual(result.status, "ready")
        self.assertEqual(result.error, "Output validation failed")
        self.assertEqual(result.validation_errors, ["output.name is required"])

    def test_returns_done_when_completion_checker_reports_done(self):
        flow_def = FlowDef(name="test_flow", max_turns=10, steps=[])
        run_state = RunState(completed={}, running=[], turn_count=0, status="in_progress")
        sut = _make_stepper(
            flow_def, snapshots=[RunSnapshot(run_state=run_state, ready=[])],
            completion_result=FlowNextResult(status="done"),
        )

        result = sut.flow_next()

        self.assertEqual(result.status, "done")

    def test_returns_timed_out_when_completion_checker_reports_timed_out(self):
        flow_def = FlowDef(name="test_flow", max_turns=1, steps=[])
        run_state = RunState(completed={}, running=[], turn_count=0, status="in_progress")
        sut = _make_stepper(
            flow_def, snapshots=[RunSnapshot(run_state=run_state, ready=[])],
            completion_result=FlowNextResult(status="timed_out"),
        )

        result = sut.flow_next()

        self.assertEqual(result.status, "timed_out")

    def test_returns_next_ready_steps_when_run_continues(self):
        flow_def = FlowDef(name="test_flow", max_turns=10, steps=[])
        run_state = RunState(completed={}, running=[], turn_count=0, status="in_progress")
        step_result = StepResult(step_id="step-b", instance_id="step-b-1", prompt="Do step-b", execution={"mode": "inline"})
        sut = _make_stepper(
            flow_def,
            snapshots=[RunSnapshot(run_state=run_state, ready=[]), RunSnapshot(run_state=run_state, ready=[])],
            completion_result=None,
            next_steps=[step_result],
        )

        result = sut.flow_next({"step-a-1": {}})

        self.assertEqual(result.status, "ready")
        self.assertEqual(result.steps, [step_result])

    def test_records_outputs_for_ready_instances_before_advancing(self):
        flow_def = FlowDef(name="test_flow", max_turns=10, steps=[])
        instance = StepInstance(step_id="step-a", instance_id="step-a-1", item=None, prompt="Do step-a")
        run_state = RunState(completed={}, running=[], turn_count=0, status="in_progress")
        stepper = FlowStepper(
            run_locator=StubRunLocator(_location()),
            metadata_store=StubMetadataStore(RunMetadata(params={}, detected_env="")),
            flow_loader=StubFlowLoader(flow_def),
            run_snapshot_resolver=StubRunSnapshotResolver([
                RunSnapshot(run_state=run_state, ready=[instance]),
                RunSnapshot(run_state=run_state, ready=[]),
            ]),
            output_validator=StubOutputValidator([]),
            session_reader=StubSessionReader(),
            output_recorder=(recorder := SpyOutputRecorder()),
            turn_advancer=StubTurnAdvancer(run_state),
            completion_checker=StubCompletionChecker(None),
            step_result_builder=StubStepResultBuilder([]),
        )

        stepper.flow_next({"step-a-1": {"result": "ok"}})

        self.assertEqual(recorder.calls, [
            ("/runs/run-1/events.jsonl", [instance], {"step-a-1": {"result": "ok"}}, "session-42"),
        ])

    def test_returns_clean_error_when_initial_snapshot_interpolation_fails(self):
        flow_def = FlowDef(name="test_flow", max_turns=10, steps=[])
        sut = _make_stepper(flow_def, snapshots=[InterpolationError("bad reference")])

        result = sut.flow_next()

        self.assertEqual(result.status, "ready")
        self.assertEqual(result.error, "bad reference")

    def test_returns_clean_error_when_next_snapshot_interpolation_fails(self):
        flow_def = FlowDef(name="test_flow", max_turns=10, steps=[])
        run_state = RunState(completed={}, running=[], turn_count=0, status="in_progress")
        sut = _make_stepper(
            flow_def,
            snapshots=[RunSnapshot(run_state=run_state, ready=[]), InterpolationError("bad reference")],
            completion_result=None,
        )

        result = sut.flow_next()

        self.assertEqual(result.status, "ready")
        self.assertEqual(result.error, "bad reference")


if __name__ == "__main__":
    unittest.main()
