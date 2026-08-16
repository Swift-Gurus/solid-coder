"""solid-name: TestInterpolator
solid-description: Validates template interpolation with variable substitution, filtering, and error handling.
solid-category: unit-test
"""

import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.builtin_attribute_reader import BuiltinAttributeReader
from harness.expression_resolver import ExpressionResolver
from harness.filtered_expression_evaluator import FilteredExpressionEvaluator
from harness.filter_resolver import FilterResolver
from harness.interpolation_error import InterpolationError
from harness.interpolation_error_factory import InterpolationErrorFactory
from harness.interpolator import Interpolator
from harness.models import StepOutputs
from harness.nested_component_accessor import NestedComponentAccessor
from harness.nested_path_resolver import NestedPathResolver
from harness.resolved_workflow_context_value import ResolvedWorkflowContextValue
from harness.run_context_builder import RunContextBuilder
from harness.run_state import RunState
from harness.step_output_expression_resolver import StepOutputExpressionResolver
from harness.workflow_context_values_mapper import WorkflowContextValuesMapper


_MISSING_ITEM = object()


class TestInterpolator(unittest.TestCase):

    def setUp(self):
        error_factory = InterpolationErrorFactory()
        expression_resolver = ExpressionResolver(
            step_output_resolver=StepOutputExpressionResolver(error_factory),
            nested_value_resolver=NestedPathResolver(
                component_accessor=NestedComponentAccessor(
                    attribute_reader=BuiltinAttributeReader()
                ),
                error_factory=error_factory,
            ),
            error_factory=error_factory,
        )
        self.interp = Interpolator(
            evaluator=FilteredExpressionEvaluator(
                expression_evaluator=expression_resolver,
                filter_resolver=FilterResolver(),
            )
        )
        self.context_builder = RunContextBuilder(
            values_mapper=WorkflowContextValuesMapper()
        )

    def _ctx(self, item=_MISSING_ITEM, **step_outputs):
        context = self.context_builder.build(
            {"output_dir": "/tmp/out"},
            RunState(
                completed={
                    step_id: StepOutputs(values=outputs)
                    for step_id, outputs in step_outputs.items()
                },
                running=[],
                turn_count=0,
                status="in_progress",
            ),
        )
        if item is _MISSING_ITEM:
            return context
        return replace(
            context,
            item=ResolvedWorkflowContextValue(present=True, value=item),
        )

    def test_renders_steps_outputs_reference(self):
        ctx = self._ctx(load_principles={"principles": ["SRP", "OCP"]})
        result = self.interp.render("Found: {{steps.load_principles.outputs.principles}}", ctx)
        self.assertIn("SRP", result)

    def test_renders_length_filter(self):
        ctx = self._ctx(load_principles={"principles": ["SRP", "OCP", "LSP"]})
        result = self.interp.render("Count: {{steps.load_principles.outputs.principles | length}}", ctx)
        self.assertEqual(result, "Count: 3")

    def test_renders_item_in_context(self):
        ctx = self._ctx(item="SRP")
        result = self.interp.render("Principle: {{item}}", ctx)
        self.assertEqual(result, "Principle: SRP")

    def test_renders_output_dir(self):
        result = self.interp.render("Dir: {{params.output_dir}}", self._ctx())
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
        ctx = self._ctx(item="x")
        with self.assertRaises(InterpolationError):
            self.interp.render("{{item | upper}}", ctx)

    def test_raises_for_malformed_steps_reference(self):
        ctx = self._ctx(a={"x": 1})
        with self.assertRaises(InterpolationError):
            self.interp.render("{{steps.a}}", ctx)


if __name__ == "__main__":
    unittest.main()
