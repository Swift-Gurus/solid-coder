"""
solid-name: test_flow_run_orchestrator
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests that the orchestrator facade delegates each operation to its dedicated coordinator.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_next_result import FlowNextResult
from harness.flow_run_orchestrator import FlowRunOrchestrator
from harness.flow_start_result import FlowStartResult
from harness.flow_status_result import FlowStatusResult


class StubStarter:
    def __init__(self, result: FlowStartResult) -> None:
        self._result = result
        self.calls: list[tuple] = []

    def flow_start(self, flow: str, params: dict | None = None, isolated: bool = False) -> FlowStartResult:
        self.calls.append((flow, params, isolated))
        return self._result


class StubStepper:
    def __init__(self, result: FlowNextResult) -> None:
        self._result = result
        self.calls: list[tuple] = []

    def flow_next(self, outputs: dict | None = None, run_id: str | None = None) -> FlowNextResult:
        self.calls.append((outputs, run_id))
        return self._result


class StubStatusReader:
    def __init__(self, result: FlowStatusResult) -> None:
        self._result = result
        self.calls: list[str | None] = []

    def flow_status(self, run_id: str | None = None) -> FlowStatusResult:
        self.calls.append(run_id)
        return self._result


class StubLockClearer:
    def __init__(self, result: str = "") -> None:
        self._result = result
        self.calls: list[str] = []

    def clear(self, run_id: str) -> str:
        self.calls.append(run_id)
        return self._result


def _no_active_run_status() -> FlowStatusResult:
    return FlowStatusResult(
        flow="", run_id="", status="no_active_run",
        turn_count=0, max_turns=0, completed=[], running=[], pending=[],
    )


def _make_orchestrator(
    starter=None, stepper=None, status_reader=None, lock_clearer=None,
) -> FlowRunOrchestrator:
    return FlowRunOrchestrator(
        starter=starter or StubStarter(FlowStartResult(run_id="", steps=[])),
        stepper=stepper or StubStepper(FlowNextResult(status="ready")),
        status_reader=status_reader or StubStatusReader(_no_active_run_status()),
        lock_clearer=lock_clearer or StubLockClearer(),
    )


class TestFlowRunOrchestrator(unittest.TestCase):

    def test_flow_start_delegates_to_starter(self):
        starter = StubStarter(FlowStartResult(run_id="run-1", steps=[]))
        sut = _make_orchestrator(starter=starter)

        result = sut.flow_start("code_review", {"key": "value"})

        self.assertEqual(result.run_id, "run-1")
        self.assertEqual(starter.calls, [("code_review", {"key": "value"}, False)])

    def test_flow_start_passes_isolated_through_to_starter(self):
        starter = StubStarter(FlowStartResult(run_id="run-1", steps=[], isolated=True))
        sut = _make_orchestrator(starter=starter)

        sut.flow_start("code_review", isolated=True)

        self.assertEqual(starter.calls, [("code_review", None, True)])

    def test_flow_next_delegates_to_stepper(self):
        stepper = StubStepper(FlowNextResult(status="done"))
        sut = _make_orchestrator(stepper=stepper)

        result = sut.flow_next({"step-a-1": {}})

        self.assertEqual(result.status, "done")
        self.assertEqual(stepper.calls, [({"step-a-1": {}}, None)])

    def test_flow_next_passes_run_id_through_to_stepper(self):
        stepper = StubStepper(FlowNextResult(status="ready"))
        sut = _make_orchestrator(stepper=stepper)

        sut.flow_next({"a-1": {}}, run_id="isolated-run")

        self.assertEqual(stepper.calls, [({"a-1": {}}, "isolated-run")])

    def test_flow_status_delegates_to_status_reader(self):
        status_reader = StubStatusReader(FlowStatusResult(
            flow="code_review", run_id="run-1", status="in_progress",
            turn_count=1, max_turns=10, completed=[], running=[], pending=[],
        ))
        sut = _make_orchestrator(status_reader=status_reader)

        result = sut.flow_status()

        self.assertEqual(result.run_id, "run-1")
        self.assertEqual(status_reader.calls, [None])

    def test_flow_status_passes_run_id_through_to_status_reader(self):
        status_reader = StubStatusReader(_no_active_run_status())
        sut = _make_orchestrator(status_reader=status_reader)

        sut.flow_status(run_id="isolated-run")

        self.assertEqual(status_reader.calls, ["isolated-run"])

    def test_flow_clear_lock_delegates_to_lock_clearer(self):
        lock_clearer = StubLockClearer("Cleared the lock for run 'run-1'.")
        sut = _make_orchestrator(lock_clearer=lock_clearer)

        result = sut.flow_clear_lock("run-1")

        self.assertEqual(result, "Cleared the lock for run 'run-1'.")
        self.assertEqual(lock_clearer.calls, ["run-1"])


if __name__ == "__main__":
    unittest.main()
