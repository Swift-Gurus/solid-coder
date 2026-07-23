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
            "id: a-1\n\nLaunch a subagent with the following prompt:\n\nDo the thing.",
        )

    def test_render_next_includes_rejection_reason_and_attempts_remaining(self):
        result = FlowNextResult(
            status="ready",
            steps=[
                StepResult(
                    step_id="a", instance_id="a-1", prompt="Do the thing.", execution={"mode": "inline"},
                    attempts_remaining=2, rejection_reason="12345 is not of type 'string'",
                )
            ],
        )

        self.assertEqual(
            self.sut.render_next(result),
            "id: a-1\nRejected: 12345 is not of type 'string'. Try again — you have 2 attempt(s) left."
            "\n\nDo the thing.",
        )

    def test_render_next_returns_done_message(self):
        self.assertEqual(self.sut.render_next(FlowNextResult(status="done")), "Flow complete.")

    def test_render_next_returns_timed_out_message(self):
        self.assertEqual(
            self.sut.render_next(FlowNextResult(status="timed_out")),
            "Flow timed out — reached the flow's max_turns limit.",
        )

    def test_render_next_returns_failed_message(self):
        self.assertEqual(
            self.sut.render_next(FlowNextResult(status="failed")),
            "Flow failed — a step exhausted its retry attempts.",
        )

    def test_render_next_returns_the_error_message_when_set(self):
        result = FlowNextResult(status="ready", error="Unresolvable reference: step 'nope' not found in context")

        self.assertEqual(
            self.sut.render_next(result),
            "Unresolvable reference: step 'nope' not found in context",
        )


if __name__ == "__main__":
    unittest.main()
