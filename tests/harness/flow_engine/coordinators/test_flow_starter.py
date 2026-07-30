"""
solid-name: test_flow_starter
solid-category: unit-test
solid-spec: [SPEC-013, SPEC-027]
solid-description: Tests coordinating flow initialization, execution/readiness resolution, and result assembly.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.active_run_location import ActiveRunLocation
from harness.execution_outcome import ExecutionOutcome
from harness.flow_init import FlowInit
from harness.flow_start_result import FlowStartResult
from harness.flow_starter import FlowStarter
from harness.models import FlowDef
from harness.step_result import StepResult


def _flow_init(run_id: str = "run-1", flow_def: FlowDef | None = None) -> FlowInit:
    return FlowInit(
        location=ActiveRunLocation(
            run_id=run_id, base_dir=Path("/runs"), run_dir=Path(f"/runs/{run_id}"),
            events_path=f"/runs/{run_id}/events.jsonl", workflow_path=f"/runs/{run_id}/workflow.yaml",
        ),
        effective_base_dir=Path("/runs"),
        flow_def=flow_def or FlowDef(name="code_review", max_turns=10, steps=[]),
    )


class StubFlowInitializer:
    def __init__(self, flow_init: FlowInit) -> None:
        self._flow_init = flow_init
        self.calls: list[tuple] = []

    def initialize(self, flow: str, params: dict, isolated: bool) -> FlowInit:
        self.calls.append((flow, params, isolated))
        return self._flow_init


class StubExecutionAndReadinessCoordinator:
    def __init__(self, outcome: ExecutionOutcome) -> None:
        self._outcome = outcome
        self.calls: list[tuple] = []

    def coordinate(self, effective_base_dir, run_id, events_path, flow_def, params) -> ExecutionOutcome:
        self.calls.append((effective_base_dir, run_id, events_path, flow_def, params))
        return self._outcome


class SpyFlowStartResultBuilder:
    def __init__(self, result: FlowStartResult) -> None:
        self._result = result
        self.calls: list[tuple] = []

    def build(self, run_id: str, outcome: ExecutionOutcome, isolated: bool) -> FlowStartResult:
        self.calls.append((run_id, outcome, isolated))
        return self._result


class FlowStarterFactory:
    """Builds a FlowStarter with sensible stub/spy defaults; tests override only what they vary."""

    def __init__(self) -> None:
        self.flow_init = _flow_init()
        self.initializer = StubFlowInitializer(self.flow_init)
        self.outcome = ExecutionOutcome(steps=[])
        self.execution_and_readiness_coordinator = StubExecutionAndReadinessCoordinator(self.outcome)
        self.result = FlowStartResult(run_id="run-1", steps=[])
        self.result_builder = SpyFlowStartResultBuilder(self.result)

    def with_flow_init(self, flow_init: FlowInit) -> "FlowStarterFactory":
        self.flow_init = flow_init
        self.initializer = StubFlowInitializer(flow_init)
        return self

    def with_execution_and_readiness_coordinator(self, coordinator) -> "FlowStarterFactory":
        self.execution_and_readiness_coordinator = coordinator
        return self

    def with_result_builder(self, builder) -> "FlowStarterFactory":
        self.result_builder = builder
        return self

    def make_sut(self) -> FlowStarter:
        return FlowStarter(
            initializer=self.initializer,
            execution_and_readiness_coordinator=self.execution_and_readiness_coordinator,
            result_builder=self.result_builder,
        )


class TestFlowStarter(unittest.TestCase):

    def test_flow_start_initializes_with_the_given_flow_params_and_isolated_flag(self):
        factory = FlowStarterFactory()

        factory.make_sut().flow_start("code_review", {"key": "value"}, isolated=True)

        self.assertEqual(factory.initializer.calls, [("code_review", {"key": "value"}, True)])

    def test_flow_start_defaults_params_to_empty_dict(self):
        factory = FlowStarterFactory()

        factory.make_sut().flow_start("code_review")

        self.assertEqual(factory.initializer.calls, [("code_review", {}, False)])

    def test_flow_start_coordinates_execution_with_the_initializer_output(self):
        flow_def = FlowDef(name="code_review", max_turns=10, steps=[])
        flow_init = _flow_init(run_id="run-9", flow_def=flow_def)
        factory = FlowStarterFactory().with_flow_init(flow_init)

        factory.make_sut().flow_start("code_review", {"key": "value"})

        self.assertEqual(factory.execution_and_readiness_coordinator.calls, [
            (Path("/runs"), "run-9", "/runs/run-9/events.jsonl", flow_def, {"key": "value"}),
        ])

    def test_flow_start_builds_the_result_from_the_coordinated_outcome(self):
        outcome = ExecutionOutcome(steps=[
            StepResult(step_id="a", instance_id="a-1", prompt="Do a", execution={"mode": "inline"}),
        ])
        flow_init = _flow_init(run_id="run-9")
        factory = FlowStarterFactory().with_flow_init(flow_init).with_execution_and_readiness_coordinator(
            StubExecutionAndReadinessCoordinator(outcome)
        )

        factory.make_sut().flow_start("code_review", isolated=True)

        self.assertEqual(factory.result_builder.calls, [("run-9", outcome, True)])

    def test_flow_start_returns_whatever_the_result_builder_produces(self):
        expected = FlowStartResult(run_id="run-1", steps=[], error="boom")
        factory = FlowStarterFactory().with_result_builder(SpyFlowStartResultBuilder(expected))

        result = factory.make_sut().flow_start("code_review")

        self.assertIs(result, expected)


if __name__ == "__main__":
    unittest.main()
