"""
solid-name: test_flow_starter
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests coordinating flow resolution, provisioning, event recording, and initial step readiness.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_starter import FlowStarter
from harness.interpolation_error import InterpolationError
from harness.models import FlowDef, RunState, StepInstance
from harness.run_init import RunInit
from harness.run_snapshot import RunSnapshot
from harness.startup_context import StartupContext
from harness.step_result import StepResult


class StubStartupContext:
    def __init__(self, context: StartupContext) -> None:
        self._context = context

    def resolve(self) -> StartupContext:
        return self._context


class StubFlowLoader:
    def __init__(self, flow_def: FlowDef) -> None:
        self._flow_def = flow_def
        self.calls: list[tuple] = []

    def load(self, path: str, search_paths: list[str]) -> FlowDef:
        self.calls.append((path, search_paths))
        return self._flow_def


class StubRunProvisioner:
    def __init__(self, run_init: RunInit) -> None:
        self._run_init = run_init
        self.calls: list[tuple] = []

    def provision(self, base_dir: Path, flow_def: FlowDef, params: dict, detected_env: str) -> RunInit:
        self.calls.append((base_dir, flow_def, params, detected_env))
        return self._run_init


class SpyEventAppender:
    def __init__(self) -> None:
        self.events: list[tuple] = []

    def append(self, path: str, event_type: str, payload: dict) -> None:
        self.events.append((path, event_type, payload))


class StubRunSnapshotResolver:
    def __init__(self, snapshot: RunSnapshot | None = None, error: InterpolationError | None = None) -> None:
        self._snapshot = snapshot
        self._error = error
        self.calls: list[tuple] = []

    def resolve(self, events_path: str, flow_def: FlowDef, params: dict) -> RunSnapshot:
        self.calls.append((events_path, flow_def, params))
        if self._error is not None:
            raise self._error
        return self._snapshot


class StubStepResultBuilder:
    def __init__(self, steps: list[StepResult]) -> None:
        self._steps = steps
        self.calls: list[tuple] = []

    def build(self, instances: list[StepInstance], flow_def: FlowDef, detected_env: str) -> list[StepResult]:
        self.calls.append((instances, flow_def, detected_env))
        return self._steps


class TestFlowStarter(unittest.TestCase):

    def test_flow_start_coordinates_load_provision_record_and_readiness(self):
        flow_def = FlowDef(name="code_review", max_turns=10, steps=[])
        run_init = RunInit(run_id="run-1", run_dir=Path("/runs/run-1"))
        instance = StepInstance(step_id="step-a", instance_id="step-a-1", item=None, prompt="Do step-a")
        run_state = RunState(completed={}, running=[], turn_count=0, status="in_progress")
        snapshot = RunSnapshot(run_state=run_state, ready=[instance])
        step_result = StepResult(step_id="step-a", instance_id="step-a-1", prompt="Do step-a", execution={"mode": "inline"})

        flow_loader = StubFlowLoader(flow_def)
        provisioner = StubRunProvisioner(run_init)
        event_appender = SpyEventAppender()
        snapshot_resolver = StubRunSnapshotResolver(snapshot)
        step_result_builder = StubStepResultBuilder([step_result])

        sut = FlowStarter(
            startup_context=StubStartupContext(StartupContext(
                detected_env="claude_code", base_dir=Path("/runs"), search_paths=["/flows"],
            )),
            flow_loader=flow_loader,
            run_provisioner=provisioner,
            event_appender=event_appender,
            run_snapshot_resolver=snapshot_resolver,
            step_result_builder=step_result_builder,
        )

        result = sut.flow_start("code_review", {"key": "value"})

        self.assertEqual(result.run_id, "run-1")
        self.assertEqual(result.steps, [step_result])
        self.assertEqual(flow_loader.calls, [("code_review", ["/flows"])])
        self.assertEqual(provisioner.calls, [(Path("/runs"), flow_def, {"key": "value"}, "claude_code")])
        self.assertEqual(event_appender.events, [
            (str(Path("/runs/run-1/events.jsonl")), "run_started", {"run_id": "run-1", "flow": "code_review"}),
        ])
        self.assertEqual(snapshot_resolver.calls, [
            (str(Path("/runs/run-1/events.jsonl")), flow_def, {"key": "value"}),
        ])
        self.assertEqual(step_result_builder.calls, [([instance], flow_def, "claude_code")])

    def test_flow_start_defaults_params_to_empty_dict(self):
        flow_def = FlowDef(name="code_review", max_turns=10, steps=[])
        run_init = RunInit(run_id="run-1", run_dir=Path("/runs/run-1"))
        run_state = RunState(completed={}, running=[], turn_count=0, status="in_progress")
        provisioner = StubRunProvisioner(run_init)

        sut = FlowStarter(
            startup_context=StubStartupContext(StartupContext(
                detected_env="", base_dir=Path("/runs"), search_paths=[],
            )),
            flow_loader=StubFlowLoader(flow_def),
            run_provisioner=provisioner,
            event_appender=SpyEventAppender(),
            run_snapshot_resolver=StubRunSnapshotResolver(RunSnapshot(run_state=run_state, ready=[])),
            step_result_builder=StubStepResultBuilder([]),
        )

        sut.flow_start("code_review")

        self.assertEqual(provisioner.calls[0][2], {})

    def test_returns_clean_error_when_prompt_interpolation_fails(self):
        flow_def = FlowDef(name="code_review", max_turns=10, steps=[])
        run_init = RunInit(run_id="run-1", run_dir=Path("/runs/run-1"))

        sut = FlowStarter(
            startup_context=StubStartupContext(StartupContext(
                detected_env="", base_dir=Path("/runs"), search_paths=[],
            )),
            flow_loader=StubFlowLoader(flow_def),
            run_provisioner=StubRunProvisioner(run_init),
            event_appender=SpyEventAppender(),
            run_snapshot_resolver=StubRunSnapshotResolver(error=InterpolationError("bad reference")),
            step_result_builder=StubStepResultBuilder([]),
        )

        result = sut.flow_start("code_review")

        self.assertEqual(result.run_id, "run-1")
        self.assertEqual(result.steps, [])
        self.assertEqual(result.error, "bad reference")


if __name__ == "__main__":
    unittest.main()
