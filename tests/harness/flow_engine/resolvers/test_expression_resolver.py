"""
solid-name: test_expression_resolver
solid-category: unit-test
solid-spec: [SPEC-034]
solid-description: Tests expression lookup for named flow parameters and actionable failures for missing parameter references.
"""

from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.builtin_attribute_reader import BuiltinAttributeReader
from harness.expression_resolver import ExpressionResolver
from harness.interpolation_error import InterpolationError
from harness.interpolation_error_factory import InterpolationErrorFactory
from harness.nested_component_accessor import NestedComponentAccessor
from harness.nested_path_resolver import NestedPathResolver
from harness.run_context_builder import RunContextBuilder
from harness.run_state import RunState
from harness.step_output_expression_resolver import StepOutputExpressionResolver
from harness.step_output_reference_parser import StepOutputReferenceParser
from harness.step_output_reference_resolver import StepOutputReferenceResolver
from harness.workflow_context_values_mapper import WorkflowContextValuesMapper


class TestExpressionResolver(unittest.TestCase):
    def setUp(self):
        self.context_builder = RunContextBuilder(
            values_mapper=WorkflowContextValuesMapper()
        )
        self.run_state = RunState(
            completed={},
            running=[],
            turn_count=0,
            status="in_progress",
        )
        error_factory = InterpolationErrorFactory()
        nested_values = NestedPathResolver(
            component_accessor=NestedComponentAccessor(
                attribute_reader=BuiltinAttributeReader()
            ),
            error_factory=error_factory,
        )
        self.sut = ExpressionResolver(
            step_output_resolver=StepOutputExpressionResolver(
                reference_parser=StepOutputReferenceParser(),
                reference_resolver=StepOutputReferenceResolver[object](error_factory),
                error_factory=error_factory,
                nested_value_resolver=nested_values,
            ),
            nested_value_resolver=nested_values,
            error_factory=error_factory,
        )

    def test_named_parameter_reference_returns_the_parameter_value(self):
        result = self.sut.evaluate(
            "params.file_path",
            self.context_builder.build(
                {"file_path": "/tmp/Foo.swift"},
                self.run_state,
            ),
        )

        self.assertEqual(result, "/tmp/Foo.swift")

    def test_missing_parameter_reference_raises_an_actionable_error(self):
        with self.assertRaisesRegex(
            InterpolationError, "parameter 'file_path' not found"
        ):
            self.sut.evaluate(
                "params.file_path",
                self.context_builder.build({}, self.run_state),
            )

    def test_resolves_nested_fields_of_a_named_step_output(self):
        state = replace(
            self.run_state,
            completed={
                "review.prepare": {
                    "review_file": {
                        "applicability": {
                            "file_extension": ".swift",
                            "tags": ["unit-test"],
                        },
                        "optional": None,
                    },
                },
            },
        )
        context = self.context_builder.build({}, state)

        for path, expected in [
            ("applicability.file_extension", ".swift"),
            ("applicability.tags", ["unit-test"]),
            ("optional", None),
        ]:
            with self.subTest(path=path):
                self.assertEqual(
                    self.sut.evaluate(
                        f"steps.review.prepare.outputs.review_file.{path}",
                        context,
                    ),
                    expected,
                )

    def test_missing_nested_output_field_reports_the_complete_reference(self):
        state = replace(self.run_state, completed={"prepare": {"review_file": {}}})
        expression = "steps.prepare.outputs.review_file.applicability.tags"

        with self.assertRaises(InterpolationError) as raised:
            self.sut.evaluate(expression, self.context_builder.build({}, state))

        self.assertIn(expression, str(raised.exception))


if __name__ == "__main__":
    unittest.main()
