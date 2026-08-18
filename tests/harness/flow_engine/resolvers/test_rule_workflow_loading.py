"""
solid-name: TestRuleWorkflowLoading
solid-category: unit-test
solid-spec: [SPEC-039]
solid-description: Verifies typed loading and structural validation of executable review-rule workflows.
"""

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_engine_assembly_factory import FlowEngineAssemblyFactory
from harness.models import FlowValidationError
from harness.rule_declaration import RuleDeclaration


class TestRuleWorkflowLoading(unittest.TestCase):
    def setUp(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.directory = Path(temporary_directory.name)
        self.loader = FlowEngineAssemblyFactory().build().flow_loader

    def test_loads_metric_and_exception_steps_as_typed_rule_declarations(self) -> None:
        flow = self.loader.load(
            self._write(
                """
                id: solid-srp-review
                name: Single Responsibility Review
                max_turns: 10
                rule:
                  category: solid
                  tags: [swift]
                steps:
                  - id: verb_count
                    type: metric
                    metric_id: SRP-1
                    prompt: Count responsibility verbs in {{params.review_unit}}.
                    value:
                      type: integer
                      minimum: 0
                    scoring:
                      minor:
                        operator: greater_than_or_equal
                        value: 3
                      severe:
                        operator: greater_than
                        value: 5
                  - id: classify_exception
                    type: exception
                    prompt: Decide whether {{params.review_unit}} is an SRP exception.
                """
            ),
            [],
        )

        self.assertEqual(
            flow.rule,
            RuleDeclaration(category="solid", tags=["swift"]),
        )
        metric = flow.steps[0]
        self.assertEqual(metric.metric.metric_id, "SRP-1")
        self.assertEqual(metric.metric.value.type, "integer")
        self.assertEqual(metric.metric.value.minimum, 0)
        self.assertEqual(
            metric.metric.scoring.minor.operator.value,
            "greater_than_or_equal",
        )
        self.assertEqual(metric.metric.scoring.minor.value, 3)
        self.assertEqual(metric.metric.scoring.severe.operator.value, "greater_than")
        self.assertEqual(metric.metric.scoring.severe.value, 5)
        self.assertEqual([output.name for output in metric.outputs], ["value", "additional_info"])
        self.assertIn('"reasoning"', metric.prompt)
        self.assertIn('"evidence"', metric.prompt)

        exception = flow.steps[1]
        self.assertEqual(exception.type, "exception")
        self.assertEqual(
            [output.name for output in exception.outputs],
            ["is_exception", "additional_info"],
        )
        self.assertIn('"is_exception"', exception.prompt)
        self.assertIn('"reasoning"', exception.prompt)
        self.assertIn('"evidence"', exception.prompt)

    def test_rejects_rule_without_a_metric_step(self) -> None:
        self._assert_invalid(
            """
            id: no-metric
            name: No Metric
            max_turns: 5
            rule: {}
            steps:
              - id: classify_exception
                type: exception
                prompt: Classify the exception.
            """,
            "at least one 'metric' step",
        )

    def test_rejects_rule_without_exactly_one_exception_step(self) -> None:
        self._assert_invalid(
            """
            id: duplicate-exception
            name: Duplicate Exception
            max_turns: 5
            rule: {}
            steps:
              - id: smell
                type: metric
                metric_id: TEST-1
                prompt: Measure the smell.
                value:
                  type: boolean
                scoring:
                  severe:
                    operator: equals
                    value: true
              - id: first_exception
                type: exception
                prompt: Classify the first exception.
              - id: second_exception
                type: exception
                prompt: Classify the second exception.
            """,
            "exactly one 'exception' step",
        )

    def test_rejects_duplicate_metric_ids(self) -> None:
        self._assert_invalid(
            """
            id: duplicate-metric
            name: Duplicate Metric
            max_turns: 5
            rule: {}
            steps:
              - id: first
                type: metric
                metric_id: TEST-1
                prompt: Measure first.
                value: {type: integer}
                scoring:
                  minor: {operator: greater_than, value: 1}
              - id: second
                type: metric
                metric_id: TEST-1
                prompt: Measure second.
                value: {type: integer}
                scoring:
                  severe: {operator: greater_than, value: 2}
              - id: classify_exception
                type: exception
                prompt: Classify the exception.
            """,
            "duplicate metric_id 'TEST-1'",
        )

    def test_rejects_non_scalar_metric_value_schema(self) -> None:
        self._assert_invalid(
            """
            id: object-metric
            name: Object Metric
            max_turns: 5
            rule: {}
            steps:
              - id: object_value
                type: metric
                metric_id: TEST-1
                prompt: Return an object.
                value: {type: object}
                scoring:
                  severe: {operator: equals, value: true}
              - id: classify_exception
                type: exception
                prompt: Classify the exception.
            """,
            "value.type",
        )

    def test_rejects_metric_band_with_unknown_operator(self) -> None:
        self._assert_invalid(
            """
            id: ambiguous-band
            name: Ambiguous Band
            max_turns: 5
            rule: {}
            steps:
              - id: ambiguous
                type: metric
                metric_id: TEST-1
                prompt: Measure ambiguity.
                value: {type: integer}
                scoring:
                  severe:
                    operator: between
                    value: 2
              - id: classify_exception
                type: exception
                prompt: Classify the exception.
            """,
            "operator",
        )

    def _assert_invalid(self, source: str, expected_message: str) -> None:
        with self.assertRaisesRegex(FlowValidationError, expected_message):
            self.loader.load(self._write(source), [])

    def _write(self, source: str) -> str:
        path = self.directory / "workflow.yaml"
        path.write_text(textwrap.dedent(source))
        return str(path)


if __name__ == "__main__":
    unittest.main()
