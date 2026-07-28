"""
solid-name: test_flow_result_json_renderer
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests rendering flow_start/flow_next results as their full JSON representation.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_next_result import FlowNextResult
from harness.flow_result_json_renderer import FlowResultJsonRenderer
from harness.flow_start_result import FlowStartResult
from harness.step_result import StepResult


class TestFlowResultJsonRenderer(unittest.TestCase):

    def setUp(self):
        self.sut = FlowResultJsonRenderer()

    def test_render_start_returns_the_full_result_as_json(self):
        result = FlowStartResult(
            run_id="r1",
            steps=[StepResult(step_id="a", instance_id="a-1", prompt="Do the thing.", execution={"mode": "inline"})],
        )

        rendered = json.loads(self.sut.render_start(result))

        self.assertEqual(rendered["run_id"], "r1")
        self.assertEqual(rendered["steps"][0]["instance_id"], "a-1")
        self.assertEqual(rendered["steps"][0]["prompt"], "Do the thing.")
        self.assertEqual(rendered["steps"][0]["execution"], {"mode": "inline"})

    def test_render_next_returns_the_full_result_as_json_including_status(self):
        result = FlowNextResult(status="done")

        rendered = json.loads(self.sut.render_next(result))

        self.assertEqual(rendered["status"], "done")
        self.assertEqual(rendered["steps"], [])
        self.assertIsNone(rendered["error"])

    def test_render_next_includes_rejection_reason(self):
        result = FlowNextResult(
            status="ready",
            steps=[
                StepResult(
                    step_id="a", instance_id="a-1", prompt="Do the thing.", execution={"mode": "inline"},
                    rejection_reason="12345 is not of type 'string'",
                )
            ],
        )

        rendered = json.loads(self.sut.render_next(result))

        self.assertEqual(rendered["steps"][0]["rejection_reason"], "12345 is not of type 'string'")


if __name__ == "__main__":
    unittest.main()
