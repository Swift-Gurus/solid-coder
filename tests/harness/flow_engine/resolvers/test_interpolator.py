"""solid-name: TestInterpolator
solid-description: Validates template interpolation with variable substitution, filtering, and error handling.
solid-category: unit-test
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.expression_resolver import ExpressionResolver
from harness.filter_resolver import FilterResolver
from harness.interpolation_error import InterpolationError
from harness.interpolator import Interpolator
from harness.models import StepOutputs


class TestInterpolator(unittest.TestCase):

    def setUp(self):
        self.interp = Interpolator(evaluator=ExpressionResolver(filter_resolver=FilterResolver()))

    def _ctx(self, **step_outputs):
        return {
            "steps": {k: StepOutputs(values=v) for k, v in step_outputs.items()},
            "output_dir": "/tmp/out",
        }

    def test_renders_steps_outputs_reference(self):
        ctx = self._ctx(load_principles={"principles": ["SRP", "OCP"]})
        result = self.interp.render("Found: {{steps.load_principles.outputs.principles}}", ctx)
        self.assertIn("SRP", result)

    def test_renders_length_filter(self):
        ctx = self._ctx(load_principles={"principles": ["SRP", "OCP", "LSP"]})
        result = self.interp.render("Count: {{steps.load_principles.outputs.principles | length}}", ctx)
        self.assertEqual(result, "Count: 3")

    def test_renders_item_in_context(self):
        ctx = {**self._ctx(), "item": "SRP"}
        result = self.interp.render("Principle: {{item}}", ctx)
        self.assertEqual(result, "Principle: SRP")

    def test_renders_output_dir(self):
        result = self.interp.render("Dir: {{output_dir}}", self._ctx())
        self.assertEqual(result, "Dir: /tmp/out")

    def test_passthrough_when_no_placeholders(self):
        result = self.interp.render("No placeholders here.", self._ctx())
        self.assertEqual(result, "No placeholders here.")

    def test_raises_for_unknown_step(self):
        ctx = self._ctx()
        with self.assertRaises(InterpolationError):
            self.interp.render("{{steps.missing.outputs.x}}", ctx)

    def test_raises_for_unknown_output(self):
        ctx = self._ctx(step_a={"x": 1})
        with self.assertRaises(InterpolationError):
            self.interp.render("{{steps.step_a.outputs.y}}", ctx)

    def test_raises_for_unknown_filter(self):
        ctx = {**self._ctx(), "item": "x"}
        with self.assertRaises(InterpolationError):
            self.interp.render("{{item | upper}}", ctx)

    def test_raises_for_malformed_steps_reference(self):
        ctx = self._ctx(a={"x": 1})
        with self.assertRaises(InterpolationError):
            self.interp.render("{{steps.a}}", ctx)


if __name__ == "__main__":
    unittest.main()
