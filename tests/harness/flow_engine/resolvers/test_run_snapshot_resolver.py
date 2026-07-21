"""
solid-name: test_run_snapshot_resolver
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests replaying a run's events, building context, and computing ready steps as one snapshot.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.models import FlowDef, RunState, StepInstance
from harness.run_snapshot_resolver import RunSnapshotResolver


class StubEventReplayer:
    def __init__(self, run_state: RunState) -> None:
        self._run_state = run_state
        self.calls: list[str] = []

    def replay(self, path: str) -> RunState:
        self.calls.append(path)
        return self._run_state


class StubContextBuilder:
    def __init__(self, context: dict) -> None:
        self._context = context
        self.calls: list[tuple] = []

    def build(self, params: dict, run_state: RunState) -> dict:
        self.calls.append((params, run_state))
        return self._context


class StubDAGRunner:
    def __init__(self, ready: list[StepInstance]) -> None:
        self._ready = ready
        self.calls: list[tuple] = []

    def ready_steps(self, flow_def: FlowDef, run_state: RunState, context: dict) -> list[StepInstance]:
        self.calls.append((flow_def, run_state, context))
        return self._ready


class TestRunSnapshotResolver(unittest.TestCase):

    def test_resolves_run_state_and_ready_steps_from_events_path(self):
        run_state = RunState(completed={}, running=[], turn_count=1, status="in_progress")
        instance = StepInstance(step_id="step-a", instance_id="step-a-1", item=None, prompt="Do step-a")
        flow_def = FlowDef(name="test_flow", max_turns=10, steps=[])
        replayer = StubEventReplayer(run_state)
        context_builder = StubContextBuilder({"params": {"key": "value"}})
        dag_runner = StubDAGRunner([instance])
        sut = RunSnapshotResolver(event_replayer=replayer, context_builder=context_builder, dag_runner=dag_runner)

        snapshot = sut.resolve("/run/events.jsonl", flow_def, {"key": "value"})

        self.assertIs(snapshot.run_state, run_state)
        self.assertEqual(snapshot.ready, [instance])
        self.assertEqual(replayer.calls, ["/run/events.jsonl"])
        self.assertEqual(context_builder.calls, [({"key": "value"}, run_state)])
        self.assertEqual(dag_runner.calls, [(flow_def, run_state, {"params": {"key": "value"}})])


if __name__ == "__main__":
    unittest.main()
