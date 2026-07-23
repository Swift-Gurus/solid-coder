"""
solid-name: test_script_failure_attributor
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests attributing a failed script step's attempt to itself or to a completed agent-type dependency.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.models import FlowDef, RunState, StepDef, StepOutputs
from harness.script_failure_attributor import ScriptFailureAttributor


class TestScriptFailureAttributor(unittest.TestCase):

    def setUp(self):
        self.sut = ScriptFailureAttributor()

    def test_attributes_to_self_when_no_completed_agent_dependency(self):
        failed = StepDef(id="gate", prompt="", type="script", command=["run.sh"])
        flow_def = FlowDef(name="f", max_turns=10, steps=[failed])
        run_state = RunState(completed={}, running=[], turn_count=0, status="in_progress")

        self.assertEqual(self.sut.attribute(failed, run_state, flow_def), "gate")

    def test_attributes_to_the_single_completed_agent_dependency(self):
        writer = StepDef(id="writer", prompt="p", type="agent")
        gate = StepDef(id="gate", prompt="", type="script", command=["run.sh"], depends_on=["writer"])
        flow_def = FlowDef(name="f", max_turns=10, steps=[writer, gate])
        run_state = RunState(completed={"writer": StepOutputs()}, running=[], turn_count=1, status="in_progress")

        self.assertEqual(self.sut.attribute(gate, run_state, flow_def), "writer")

    def test_ignores_completed_script_dependency(self):
        upstream_script = StepDef(id="prep", prompt="", type="script", command=["prep.sh"])
        gate = StepDef(id="gate", prompt="", type="script", command=["run.sh"], depends_on=["prep"])
        flow_def = FlowDef(name="f", max_turns=10, steps=[upstream_script, gate])
        run_state = RunState(completed={"prep": StepOutputs()}, running=[], turn_count=1, status="in_progress")

        self.assertEqual(self.sut.attribute(gate, run_state, flow_def), "gate")

    def test_attributes_to_most_recently_completed_dependency_on_tie(self):
        first = StepDef(id="first", prompt="p", type="agent")
        second = StepDef(id="second", prompt="p", type="agent")
        gate = StepDef(id="gate", prompt="", type="script", command=["run.sh"], depends_on=["first", "second"])
        flow_def = FlowDef(name="f", max_turns=10, steps=[first, second, gate])
        run_state = RunState(
            completed={"first": StepOutputs(), "second": StepOutputs()},
            running=[], turn_count=2, status="in_progress",
        )

        self.assertEqual(self.sut.attribute(gate, run_state, flow_def), "second")


if __name__ == "__main__":
    unittest.main()
