"""
solid-name: test_flow_result_renderer
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests rendering flow_start/flow_next results into the plain text the calling agent sees.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.delegate_instruction_builder import build_delegate_instruction
from harness.flow_next_result import FlowNextResult
from harness.flow_result_renderer import FlowResultRenderer
from harness.flow_start_result import FlowStartResult
from harness.step_result import StepResult


class TestFlowResultRenderer(unittest.TestCase):

    def setUp(self):
        self.sut = FlowResultRenderer()

    def test_render_start_renders_a_single_ready_step(self):
        result = FlowStartResult(
            run_id="r1",
            steps=[StepResult(step_id="a", instance_id="a-1", prompt="Do the thing.", execution={"mode": "inline"})],
        )

        self.assertEqual(self.sut.render_start(result), "id: a-1\n\nDo the thing.")

    def test_render_start_discloses_run_id_when_isolated(self):
        result = FlowStartResult(
            run_id="r1",
            steps=[StepResult(step_id="a", instance_id="a-1", prompt="Do the thing.", execution={"mode": "inline"})],
            isolated=True,
        )

        self.assertEqual(
            self.sut.render_start(result),
            'run_id: r1\n\nPass run_id="r1" on every flow_next/flow_status call for this run.'
            "\n\nid: a-1\n\nDo the thing.",
        )

    def test_render_start_does_not_disclose_run_id_when_not_isolated(self):
        result = FlowStartResult(
            run_id="r1",
            steps=[StepResult(step_id="a", instance_id="a-1", prompt="Do the thing.", execution={"mode": "inline"})],
        )

        self.assertEqual(self.sut.render_start(result), "id: a-1\n\nDo the thing.")

    def test_render_start_returns_the_error_message_when_set(self):
        result = FlowStartResult(run_id="r1", steps=[], error="Flow file not found or unreadable: 'x'")

        self.assertEqual(self.sut.render_start(result), "Flow file not found or unreadable: 'x'")

    def test_render_next_renders_multiple_ready_steps_separated(self):
        result = FlowNextResult(
            status="ready",
            steps=[
                StepResult(step_id="a", instance_id="a-1", prompt="Step A.", execution={"mode": "inline"}),
                StepResult(step_id="b", instance_id="b-1", prompt="Step B.", execution={"mode": "inline"}),
            ],
        )

        self.assertEqual(
            self.sut.render_next(result),
            "id: a-1\n\nStep A.\n\n---\n\nid: b-1\n\nStep B.",
        )

    def test_render_next_wraps_subagent_steps_with_a_launch_instruction(self):
        result = FlowNextResult(
            status="ready",
            steps=[StepResult(step_id="a", instance_id="a-1", prompt="Do the thing.", execution={"mode": "subagent"})],
        )

        self.assertEqual(
            self.sut.render_next(result),
            f"id: a-1\n\nLaunch a subagent with the following prompt:\n\n{build_delegate_instruction('Do the thing.')}",
        )

    def test_render_next_includes_rejection_reason_without_exposing_attempt_counts(self):
        result = FlowNextResult(
            status="ready",
            steps=[
                StepResult(
                    step_id="a", instance_id="a-1", prompt="Do the thing.", execution={"mode": "inline"},
                    rejection_reason="12345 is not of type 'string'",
                )
            ],
        )

        self.assertEqual(
            self.sut.render_next(result),
            "id: a-1\nRejected: 12345 is not of type 'string'. Try again."
            "\n\nDo the thing.",
        )

    def test_render_next_returns_done_message(self):
        self.assertEqual(self.sut.render_next(FlowNextResult(status="done")), "Flow complete.")

    def test_render_next_returns_the_timed_out_error_message_when_set(self):
        result = FlowNextResult(status="timed_out", error="Flow timed out — step 'a' still pending.")

        self.assertEqual(self.sut.render_next(result), "Flow timed out — step 'a' still pending.")

    def test_render_next_returns_the_failed_error_message_when_set(self):
        result = FlowNextResult(status="failed", error="Flow failed — step 'a' exhausted all 3 attempt(s).")

        self.assertEqual(self.sut.render_next(result), "Flow failed — step 'a' exhausted all 3 attempt(s).")

    def test_render_next_returns_the_error_message_when_set(self):
        result = FlowNextResult(status="ready", error="Unresolvable reference: step 'nope' not found in context")

        self.assertEqual(
            self.sut.render_next(result),
            "Unresolvable reference: step 'nope' not found in context",
        )

    def test_render_next_uses_the_injected_delegate_instruction_builder(self):
        sut = FlowResultRenderer(delegate_instruction_builder=StubDelegateInstructionBuilder())
        result = FlowNextResult(
            status="ready",
            steps=[StepResult(step_id="a", instance_id="a-1", prompt="Do the thing.", execution={"mode": "subagent"})],
        )

        self.assertEqual(
            sut.render_next(result),
            "id: a-1\n\nLaunch a subagent with the following prompt:\n\nSTUB[Do the thing.]",
        )


class StubDelegateInstructionBuilder:
    def build(self, prompt: str) -> str:
        return f"STUB[{prompt}]"


if __name__ == "__main__":
    unittest.main()
