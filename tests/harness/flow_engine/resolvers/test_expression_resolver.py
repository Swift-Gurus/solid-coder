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
from harness.step_output_expression_resolver import StepOutputExpressionResolver  # noqa: E402


class TestExpressionResolver(unittest.TestCase):

    def setUp(self):
        error_factory = InterpolationErrorFactory()
        self.sut = ExpressionResolver(
            step_output_resolver=StepOutputExpressionResolver(error_factory),
            nested_value_resolver=NestedPathResolver(
                component_accessor=NestedComponentAccessor(
                    attribute_reader=BuiltinAttributeReader()
                ),
                error_factory=error_factory,
            ),
            error_factory=error_factory,
        )

    def test_named_parameter_reference_returns_the_parameter_value(self):
        result = self.sut.evaluate("params.file_path", {"params": {"file_path": "/tmp/Foo.swift"}})

        self.assertEqual(result, "/tmp/Foo.swift")

    def test_missing_parameter_reference_raises_an_actionable_error(self):
        with self.assertRaisesRegex(InterpolationError, "parameter 'file_path' not found"):
            self.sut.evaluate("params.file_path", {"params": {}})


if __name__ == "__main__":
    unittest.main()
