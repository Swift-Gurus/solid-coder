"""Validates typed collection metric reducer declarations."""

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_engine_assembly_factory import FlowEngineAssemblyFactory
from harness.models import FlowValidationError

"""
solid-name: TestCollectionMetricReducerLoading
solid-category: unit-test
solid-spec: [SPEC-054]
solid-description: Verifies sealed reducer parsing and source-schema compatibility.
"""


class TestCollectionMetricReducerLoading(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.loader = FlowEngineAssemblyFactory().build().flow_loader

    def test_loads_maximum_projection(self) -> None:
        flow = self._load(self._maximum_workflow())

        reducer = flow.steps[1].metric_calculation.reducer
        self.assertEqual(reducer.type.value, "maximum")
        self.assertEqual(reducer.value.value, "item.depth")

    def test_loads_authored_empty_value_for_numeric_extreme(self) -> None:
        workflow = self._maximum_workflow().replace(
            '                        value: "{{item.depth}}"',
            '                        value: "{{item.depth}}"\n'
            "                        empty_value: 0",
        )

        flow = self._load(workflow)

        self.assertEqual(
            flow.steps[1].metric_calculation.reducer.empty_value,
            0,
        )

    def test_loads_ratio_conditions(self) -> None:
        flow = self._load(self._ratio_workflow())

        reducer = flow.steps[1].metric_calculation.reducer
        self.assertEqual(reducer.type.value, "ratio")
        self.assertIsNotNone(reducer.numerator_condition)
        self.assertIsNotNone(reducer.denominator_condition)

    def test_rejects_maximum_without_value_projection(self) -> None:
        workflow = self._maximum_workflow().replace(
            '                        value: "{{item.depth}}"\n',
            "",
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            r"maximum\.value\s+Field required",
        ):
            self._load(workflow)

    def test_rejects_fractional_empty_value_for_integer_metric(self) -> None:
        workflow = self._maximum_workflow().replace(
            '                        value: "{{item.depth}}"',
            '                        value: "{{item.depth}}"\n'
            "                        empty_value: 0.5",
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "empty_value must match metric value type integer",
        ):
            self._load(workflow)

    def test_rejects_ratio_with_value_projection(self) -> None:
        workflow = self._ratio_workflow().replace(
            "                        numerator_when:",
            '                        value: "{{item.depth}}"\n'
            "                        numerator_when:",
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            r"ratio\.value\s+Extra inputs are not permitted",
        ):
            self._load(workflow)

    def test_rejects_ratio_for_integer_metric(self) -> None:
        workflow = self._ratio_workflow().replace(
            "type: number",
            "type: integer",
            1,
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "ratio reducer metric value must be a number",
        ):
            self._load(workflow)

    def test_rejects_distinct_count_for_non_integer_metric(self) -> None:
        workflow = (
            self._maximum_workflow()
            .replace(
                "type: maximum",
                "type: distinct_count",
                1,
            )
            .replace(
                "value: {type: integer, minimum: 0}",
                "value: {type: number, minimum: 0}",
                1,
            )
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "distinct_count reducer metric value must be an integer",
        ):
            self._load(workflow)

    def test_rejects_projection_field_absent_from_item_schema(self) -> None:
        workflow = self._maximum_workflow().replace(
            "item.depth",
            "item.missing_depth",
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "reducer value item field 'missing_depth' is not declared",
        ):
            self._load(workflow)

    def test_rejects_nonnumeric_maximum_projection(self) -> None:
        workflow = self._maximum_workflow().replace(
            "depth: {type: integer}",
            "depth: {type: string}",
            1,
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "maximum reducer value must reference an item field with schema "
            "type integer or number",
        ):
            self._load(workflow)

    def test_rejects_nonscalar_distinct_count_projection(self) -> None:
        workflow = (
            self._maximum_workflow()
            .replace(
                "type: maximum",
                "type: distinct_count",
                1,
            )
            .replace(
                "depth: {type: integer}",
                "depth: {type: object}",
                1,
            )
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "distinct_count reducer value must reference an item field with "
            "schema type integer or number or string or boolean or null",
        ):
            self._load(workflow)

    def test_rejects_ratio_condition_field_absent_from_item_schema(self) -> None:
        workflow = self._ratio_workflow().replace(
            "item.classification",
            "item.missing_classification",
            1,
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "reducer numerator_when item field 'missing_classification' is "
            "not declared",
        ):
            self._load(workflow)

    def _load(self, workflow: str):
        path = self.directory / "workflow.yaml"
        path.write_text(textwrap.dedent(workflow), encoding="utf-8")
        return self.loader.load(str(path), [])

    def _maximum_workflow(self) -> str:
        return """
                id: depth-review
                name: Depth Review
                max_turns: 5
                rule: {}
                steps:
                  - id: analyze_views
                    prompt: Classify view expressions.
                    outputs:
                      - name: views
                        type: data
                        schema:
                          type: array
                          items:
                            type: object
                            additionalProperties: false
                            required: [depth, is_exception]
                            properties:
                              depth: {type: integer}
                              is_exception: {type: boolean}
                  - id: maximum_depth
                    type: metric
                    metric_id: DEPTH-1
                    depends_on: [analyze_views]
                    value: {type: integer, minimum: 0}
                    scoring:
                      source: "{{steps.analyze_views.outputs.views}}"
                      when:
                        ref: "{{item.is_exception}}"
                        equals: false
                      reducer:
                        type: maximum
                        value: "{{item.depth}}"
                      severe: {operator: greater_than_or_equal, value: 5}
                  - id: classify_exception
                    type: exception
                    prompt: Classify the whole-rule exception.
                """

    def _ratio_workflow(self) -> str:
        return """
                id: ratio-review
                name: Ratio Review
                max_turns: 5
                rule: {}
                steps:
                  - id: classify_items
                    prompt: Classify items.
                    outputs:
                      - name: items
                        type: data
                        schema:
                          type: array
                          items:
                            type: object
                            additionalProperties: false
                            required: [classification, is_exception, depth]
                            properties:
                              classification: {type: string}
                              is_exception: {type: boolean}
                              depth: {type: integer}
                  - id: unsafe_ratio
                    type: metric
                    metric_id: RATIO-1
                    depends_on: [classify_items]
                    value: {type: number, minimum: 0, maximum: 1}
                    scoring:
                      source: "{{steps.classify_items.outputs.items}}"
                      reducer:
                        type: ratio
                        numerator_when:
                          ref: "{{item.classification}}"
                          equals: UNSAFE
                        denominator_when:
                          ref: "{{item.is_exception}}"
                          equals: false
                      severe: {operator: greater_than_or_equal, value: 0.5}
                  - id: classify_exception
                    type: exception
                    prompt: Classify the whole-rule exception.
                """


if __name__ == "__main__":
    unittest.main()
