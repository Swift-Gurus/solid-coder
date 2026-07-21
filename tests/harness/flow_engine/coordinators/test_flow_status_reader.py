"""
solid-name: test_flow_status_reader
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests reading the active run's status snapshot, and the no-active-run fallback.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.active_run_location import ActiveRunLocation
from harness.flow_status_reader import FlowStatusReader
from harness.models import FlowDef, RunState, StepInstance
from harness.run_snapshot import RunSnapshot


class RaisingRunLocator:
    def locate(self) -> ActiveRunLocation:
        raise FileNotFoundError("No active run")


class StubRunLocator:
    def __init__(self, location: ActiveRunLocation) -> None:
        self._location = location

    def locate(self) -> ActiveRunLocation:
        return self._location


class StubFlowLoader:
    def __init__(self, flow_def: FlowDef) -> None:
        self._flow_def = flow_def

    def load(self, path: str, search_paths: list[str]) -> FlowDef:
        return self._flow_def


class StubRunSnapshotResolver:
    def __init__(self, snapshot: RunSnapshot) -> None:
        self._snapshot = snapshot

    def resolve(self, events_path: str, flow_def: FlowDef, params: dict) -> RunSnapshot:
        return self._snapshot


class TestFlowStatusReader(unittest.TestCase):

    def test_returns_no_active_run_when_locator_raises_file_not_found(self):
        sut = FlowStatusReader(
            run_locator=RaisingRunLocator(),
            flow_loader=StubFlowLoader(FlowDef(name="", max_turns=0, steps=[])),
            run_snapshot_resolver=StubRunSnapshotResolver(RunSnapshot(
                run_state=RunState(completed={}, running=[], turn_count=0, status="not_started"), ready=[],
            )),
        )

        result = sut.flow_status()

        self.assertEqual(result.status, "no_active_run")
        self.assertEqual(result.run_id, "")

    def test_returns_status_snapshot_for_active_run(self):
        location = ActiveRunLocation(
            run_id="run-1", base_dir=Path("/runs"), run_dir=Path("/runs/run-1"),
            events_path="/runs/run-1/events.jsonl", workflow_path="/runs/run-1/workflow.yaml",
        )
        flow_def = FlowDef(name="code_review", max_turns=10, steps=[])
        instance = StepInstance(step_id="step-b", instance_id="step-b-1", item=None, prompt="Do step-b")
        run_state = RunState(completed={"step-a": None}, running=["step-b"], turn_count=1, status="in_progress")
        sut = FlowStatusReader(
            run_locator=StubRunLocator(location),
            flow_loader=StubFlowLoader(flow_def),
            run_snapshot_resolver=StubRunSnapshotResolver(RunSnapshot(run_state=run_state, ready=[instance])),
        )

        result = sut.flow_status()

        self.assertEqual(result.flow, "code_review")
        self.assertEqual(result.run_id, "run-1")
        self.assertEqual(result.status, "in_progress")
        self.assertEqual(result.turn_count, 1)
        self.assertEqual(result.max_turns, 10)
        self.assertEqual(result.completed, ["step-a"])
        self.assertEqual(result.running, ["step-b"])
        self.assertEqual(result.pending, ["step-b"])


if __name__ == "__main__":
    unittest.main()
