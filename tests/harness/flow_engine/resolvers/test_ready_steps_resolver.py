"""
solid-name: test_ready_steps_resolver
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests resolving the current run snapshot and building step results for its ready instances.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from doubles import StubRunSnapshotResolver
from harness.models import FlowDef, RunState, StepInstance
from harness.ready_steps_resolver import ReadyStepsResolver
from harness.run_snapshot import RunSnapshot
from harness.step_result import StepResult


class StubStepResultBuilder:
    def __init__(self, steps: list[StepResult]) -> None:
        self._steps = steps
        self.calls: list[tuple] = []

    def build(self, instances, flow_def, detected_env, run_state) -> list[StepResult]:
        self.calls.append((instances, flow_def, detected_env, run_state))
        return self._steps


class TestReadyStepsResolver(unittest.TestCase):

    def test_builds_step_results_from_the_resolved_snapshot(self):
        flow_def = FlowDef(name="f", max_turns=10, steps=[])
        instance = StepInstance(step_id="a", instance_id="a-1", item=None, prompt="p")
        run_state = RunState(completed={}, running=[], turn_count=0, status="in_progress")
        snapshot = RunSnapshot(run_state=run_state, ready=[instance])
        step_result = StepResult(step_id="a", instance_id="a-1", prompt="p", execution={})
        snapshot_resolver = StubRunSnapshotResolver(snapshot)
        builder = StubStepResultBuilder([step_result])
        sut = ReadyStepsResolver(run_snapshot_resolver=snapshot_resolver, step_result_builder=builder)

        steps = sut.resolve("events.jsonl", flow_def, {"k": "v"}, "claude_code")

        self.assertEqual(steps, [step_result])
        self.assertEqual(snapshot_resolver.calls, [("events.jsonl", flow_def, {"k": "v"})])
        self.assertEqual(builder.calls, [([instance], flow_def, "claude_code", run_state)])


if __name__ == "__main__":
    unittest.main()
