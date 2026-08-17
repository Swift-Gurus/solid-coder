"""
solid-name: test_expression_resolver
solid-category: unit-test
solid-spec: [SPEC-034]
solid-description: Tests expression lookup for named flow parameters and actionable failures for missing parameter references.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.builtin_attribute_reader import BuiltinAttributeReader  # noqa: E402
from harness.expression_resolver import ExpressionResolver  # noqa: E402
from harness.interpolation_error import InterpolationError  # noqa: E402
from harness.interpolation_error_factory import InterpolationErrorFactory  # noqa: E402
from harness.nested_component_accessor import NestedComponentAccessor  # noqa: E402
from harness.nested_path_resolver import NestedPathResolver  # noqa: E402
from harness.run_context_builder import RunContextBuilder  # noqa: E402
from harness.run_state import RunState  # noqa: E402
from harness.step_output_expression_resolver import StepOutputExpressionResolver  # noqa: E402
from harness.step_output_reference_parser import StepOutputReferenceParser  # noqa: E402
from harness.step_output_reference_resolver import StepOutputReferenceResolver  # noqa: E402
from harness.workflow_context_values_mapper import WorkflowContextValuesMapper  # noqa: E402


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
        self.sut = ExpressionResolver(
            step_output_resolver=StepOutputExpressionResolver(
                reference_parser=StepOutputReferenceParser(),
                reference_resolver=StepOutputReferenceResolver[object](
                    error_factory
                ),
                error_factory=error_factory,
            ),
            nested_value_resolver=NestedPathResolver(
                component_accessor=NestedComponentAccessor(
                    attribute_reader=BuiltinAttributeReader()
                ),
                error_factory=error_factory,
            ),
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
        with self.assertRaisesRegex(InterpolationError, "parameter 'file_path' not found"):
            self.sut.evaluate(
                "params.file_path",
                self.context_builder.build({}, self.run_state),
            )


if __name__ == "__main__":
    unittest.main()
