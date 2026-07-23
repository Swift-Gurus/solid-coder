"""
solid-name: test_flow_starter
solid-category: unit-test
solid-spec: [SPEC-013, SPEC-027]
solid-description: Tests coordinating flow resolution, provisioning, event recording, script step auto-execution, and initial step readiness.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_next_result import FlowNextResult
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

    def build(self, instances, flow_def, detected_env, run_state) -> list[StepResult]:
        self.calls.append((instances, flow_def, detected_env, run_state))
        return self._steps


class StubStepExecutionCoordinator:
    def __init__(self, result: FlowNextResult | None = None) -> None:
        self._result = result
        self.calls: list[tuple] = []

    def run_ready(self, base_dir, run_id, events_path, flow_def, params):
        self.calls.append((base_dir, run_id, events_path, flow_def, params))
        return self._result


class FlowStarterFactory:
    """Builds a FlowStarter with sensible stub/spy defaults; tests override only what they vary."""

    def __init__(self) -> None:
        self.startup_context = StubStartupContext(StartupContext(
            detected_env="claude_code", base_dir=Path("/runs"), search_paths=["/flows"],
        ))
        self.flow_loader = StubFlowLoader(FlowDef(name="code_review", max_turns=10, steps=[]))
        self.run_provisioner = StubRunProvisioner(RunInit(run_id="run-1", run_dir=Path("/runs/run-1")))
        self.event_appender = SpyEventAppender()
        self.run_snapshot_resolver = StubRunSnapshotResolver(RunSnapshot(
            run_state=RunState(completed={}, running=[], turn_count=0, status="in_progress"), ready=[],
        ))
        self.step_result_builder = StubStepResultBuilder([])
        self.step_execution_coordinator = StubStepExecutionCoordinator(None)

    def with_flow_loader(self, flow_loader) -> "FlowStarterFactory":
        self.flow_loader = flow_loader
        return self

    def with_run_provisioner(self, run_provisioner) -> "FlowStarterFactory":
        self.run_provisioner = run_provisioner
        return self

    def with_run_snapshot_resolver(self, resolver) -> "FlowStarterFactory":
        self.run_snapshot_resolver = resolver
        return self

    def with_step_result_builder(self, builder) -> "FlowStarterFactory":
        self.step_result_builder = builder
        return self

    def with_step_execution_coordinator(self, coordinator) -> "FlowStarterFactory":
        self.step_execution_coordinator = coordinator
        return self

    def make_sut(self) -> FlowStarter:
        return FlowStarter(
            startup_context=self.startup_context,
            flow_loader=self.flow_loader,
            run_provisioner=self.run_provisioner,
            event_appender=self.event_appender,
            run_snapshot_resolver=self.run_snapshot_resolver,
            step_result_builder=self.step_result_builder,
            step_execution_coordinator=self.step_execution_coordinator,
        )


class TestFlowStarter(unittest.TestCase):

    def test_flow_start_returns_the_provisioned_run_id_and_built_steps(self):
        step_result = StepResult(step_id="step-a", instance_id="step-a-1", prompt="Do step-a", execution={"mode": "inline"})
        factory = FlowStarterFactory().with_step_result_builder(StubStepResultBuilder([step_result]))

        result = factory.make_sut().flow_start("code_review", {"key": "value"})

        self.assertEqual(result.run_id, "run-1")
        self.assertEqual(result.steps, [step_result])

    def test_flow_start_loads_the_flow_by_name_with_the_startup_search_paths(self):
        flow_def = FlowDef(name="code_review", max_turns=10, steps=[])
        flow_loader = StubFlowLoader(flow_def)
        factory = FlowStarterFactory().with_flow_loader(flow_loader)

        factory.make_sut().flow_start("code_review", {"key": "value"})

        self.assertEqual(flow_loader.calls, [("code_review", ["/flows"])])

    def test_flow_start_provisions_the_run_with_the_resolved_startup_context(self):
        flow_def = FlowDef(name="code_review", max_turns=10, steps=[])
        provisioner = StubRunProvisioner(RunInit(run_id="run-1", run_dir=Path("/runs/run-1")))
        factory = FlowStarterFactory().with_flow_loader(StubFlowLoader(flow_def)).with_run_provisioner(provisioner)

        factory.make_sut().flow_start("code_review", {"key": "value"})

        self.assertEqual(provisioner.calls, [(Path("/runs"), flow_def, {"key": "value"}, "claude_code")])

    def test_flow_start_appends_a_run_started_event(self):
        factory = FlowStarterFactory()

        factory.make_sut().flow_start("code_review", {"key": "value"})

        self.assertEqual(factory.event_appender.events, [
            (str(Path("/runs/run-1/events.jsonl")), "run_started", {"run_id": "run-1", "flow": "code_review"}),
        ])

    def test_flow_start_resolves_the_snapshot_and_builds_step_results_from_it(self):
        flow_def = FlowDef(name="code_review", max_turns=10, steps=[])
        factory = FlowStarterFactory().with_flow_loader(StubFlowLoader(flow_def))

        factory.make_sut().flow_start("code_review", {"key": "value"})

        self.assertEqual(factory.run_snapshot_resolver.calls, [
            (str(Path("/runs/run-1/events.jsonl")), flow_def, {"key": "value"}),
        ])

    def test_flow_start_triggers_step_execution_coordinator_before_building_steps(self):
        flow_def = FlowDef(name="code_review", max_turns=10, steps=[])
        factory = FlowStarterFactory().with_flow_loader(StubFlowLoader(flow_def))

        factory.make_sut().flow_start("code_review", {"key": "value"})

        self.assertEqual(factory.step_execution_coordinator.calls, [
            (Path("/runs"), "run-1", str(Path("/runs/run-1/events.jsonl")), flow_def, {"key": "value"}),
        ])

    def test_flow_start_defaults_params_to_empty_dict(self):
        provisioner = StubRunProvisioner(RunInit(run_id="run-1", run_dir=Path("/runs/run-1")))
        sut = FlowStarterFactory().with_run_provisioner(provisioner).make_sut()

        sut.flow_start("code_review")

        self.assertEqual(provisioner.calls[0][2], {})

    def test_returns_clean_error_when_prompt_interpolation_fails(self):
        sut = FlowStarterFactory().with_run_snapshot_resolver(
            StubRunSnapshotResolver(error=InterpolationError("bad reference"))
        ).make_sut()

        result = sut.flow_start("code_review")

        self.assertEqual(result.run_id, "run-1")
        self.assertEqual(result.steps, [])
        self.assertEqual(result.error, "bad reference")

    def test_returns_error_when_step_execution_coordinator_reports_a_terminal_result(self):
        sut = FlowStarterFactory().with_step_execution_coordinator(
            StubStepExecutionCoordinator(FlowNextResult(status="failed"))
        ).make_sut()

        result = sut.flow_start("code_review")

        self.assertEqual(result.run_id, "run-1")
        self.assertEqual(result.steps, [])
        self.assertIsNotNone(result.error)


if __name__ == "__main__":
    unittest.main()
