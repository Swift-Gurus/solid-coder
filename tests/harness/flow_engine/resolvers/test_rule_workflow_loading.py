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
from harness.rule_match_declaration import RuleMatchDeclaration
from harness.rule_selection import RuleSelection
from harness.workflow_persister_factory import make_workflow_persister


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
                  match:
                    file_extensions:
                      included: [.swift]
                    tags:
                      included: [ui]
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
            RuleDeclaration(
                match=RuleMatchDeclaration(
                    file_extensions=RuleSelection(included=[".swift"]),
                    tags=RuleSelection(included=["ui"]),
                ),
            ),
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

    def test_expands_all_marked_rules_in_stable_id_order(self) -> None:
        flow = self._load_composite_rules()

        self.assertEqual(
            [step.id for step in flow.steps],
            [
                "rule_reviews.a-rule.measure",
                "rule_reviews.a-rule.classify_exception",
                "rule_reviews.z-rule.measure",
                "rule_reviews.z-rule.classify_exception",
            ],
        )
        self.assertEqual(
            [group.alias for group in flow.alias_groups],
            ["rule_reviews.a-rule", "rule_reviews.z-rule"],
        )
        self.assertEqual(
            [
                group.rule_workflow.workflow_id
                for group in flow.alias_groups
                if group.rule_workflow is not None
            ],
            ["a-rule", "z-rule"],
        )
        self.assertEqual(
            flow.workflow_ids,
            ["composite-review", "a-rule", "z-rule"],
        )
        conditions = [group.condition for group in flow.alias_groups]
        self.assertEqual(
            [condition.conditions[0].expected for condition in conditions],
            [[".py"], [".swift"]],
        )

    def test_preserves_included_rule_ownership_through_snapshot_reload(self) -> None:
        flow = self._load_composite_rules()
        run_directory = self.directory / "run"
        run_directory.mkdir()

        make_workflow_persister().persist(run_directory, flow)
        reloaded = self.loader.load(str(run_directory / "workflow.yaml"), [])

        self.assertEqual(
            [
                group.rule_workflow.workflow_id
                for group in reloaded.alias_groups
                if group.rule_workflow is not None
            ],
            ["a-rule", "z-rule"],
        )

    def test_preserves_combined_presentation_across_rules_all_expansion(self) -> None:
        self._write_package(
            "srp",
            self._rule_source("srp", ".swift", "service"),
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "Combined presentation rule 'srp' must contain exactly one agent step",
        ):
            self.loader.load(
                self._write_package(
                    "combined-review",
                    """
                    id: combined-review
                    name: Combined Review
                    max_turns: 20
                    steps:
                      - id: prepare
                        prompt: Prepare review units.
                        outputs:
                          - name: units
                            type: data
                            schema:
                              type: array
                              items:
                                type: object
                      - include:
                          rules: all
                        as: rule_reviews
                        depends_on: [prepare]
                        presentation:
                          mode: combined
                        for_each:
                          source: "{{steps.prepare.outputs.units}}"
                          mode: batch
                          label: "{{item.target.name}}"
                        with:
                          review_unit: "{{item}}"
                    """,
                ),
                [str(self.directory)],
            )

    def test_rejects_invalid_included_rule_under_its_own_identity(self) -> None:
        self._write_package(
            "invalid-rule",
            """
            id: invalid-rule
            name: Invalid Rule
            max_turns: 5
            rule: {}
            steps:
              - id: classify_exception
                type: exception
                prompt: Classify the exception.
            """,
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "Rule workflow 'invalid-rule' must declare at least one 'metric' step",
        ):
            self.loader.load(
                self._write_composite(),
                [str(self.directory)],
            )

    def _load_composite_rules(self):
        self._write_package(
            "z-rule",
            self._rule_source("z-rule", ".swift", "swiftui"),
        )
        self._write_package(
            "a-rule",
            self._rule_source("a-rule", ".py", "test"),
        )
        return self.loader.load(
            self._write_composite(),
            [str(self.directory)],
        )

    def _write_composite(self) -> str:
        return self._write_package(
            "review",
            """
            id: composite-review
            name: Composite Review
            max_turns: 20
            steps:
              - include:
                  rules: all
                as: rule_reviews
                with:
                  review_unit: "{{params.review_unit}}"
            """,
        )

    def _rule_source(self, workflow_id: str, extension: str, tag: str) -> str:
        return f"""
        id: {workflow_id}
        name: {workflow_id}
        max_turns: 5
        rule:
          match:
            file_extensions:
              included: [{extension}]
            tags:
              included: [{tag}]
        steps:
          - id: measure
            type: metric
            metric_id: {workflow_id.upper()}-1
            prompt: Measure the unit.
            value:
              type: boolean
            scoring:
              severe:
                operator: equals
                value: true
          - id: classify_exception
            type: exception
            prompt: Classify the exception.
        """

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

    def test_rejects_ambiguous_rule_match_before_execution(self) -> None:
        self._assert_invalid(
            """
            id: ambiguous-match
            name: Ambiguous Match
            max_turns: 5
            rule:
              match:
                tags:
                  included: [test]
                  excluded: [test]
            steps:
              - id: smell
                type: metric
                metric_id: TEST-1
                prompt: Measure the smell.
                value: {type: boolean}
                scoring:
                  severe: {operator: equals, value: true}
              - id: classify_exception
                type: exception
                prompt: Classify the exception.
            """,
            "included and excluded",
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
            "Duplicate metric_id in rule workflow duplicate-metric: 'TEST-1'",
        )

    def test_allows_distinct_observations_for_one_metric_id(self) -> None:
        flow = self.loader.load(
            self._write(
                """
                id: composite-metric
                name: Composite Metric
                max_turns: 5
                rule: {}
                steps:
                  - id: nesting
                    type: metric
                    metric_id: SUI-1
                    observation_id: body_nesting_depth
                    prompt: Measure nesting.
                    value: {type: integer, minimum: 0}
                    scoring:
                      severe: {operator: greater_than_or_equal, value: 2}
                  - id: expressions
                    type: metric
                    metric_id: SUI-1
                    observation_id: view_expression_count
                    prompt: Measure expressions.
                    value: {type: integer, minimum: 0}
                    scoring:
                      severe: {operator: greater_than_or_equal, value: 5}
                  - id: classify_exception
                    type: exception
                    prompt: Classify the exception.
                """
            ),
            [],
        )

        self.assertEqual(
            [step.metric.observation_id for step in flow.steps if step.metric],
            ["body_nesting_depth", "view_expression_count"],
        )
        run_directory = self.directory / "composite-metric-run"
        run_directory.mkdir()
        make_workflow_persister().persist(run_directory, flow)

        reloaded = self.loader.load(str(run_directory / "workflow.yaml"), [])

        self.assertEqual(
            [step.metric.observation_id for step in reloaded.steps if step.metric],
            ["body_nesting_depth", "view_expression_count"],
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

    def _write_package(self, name: str, source: str) -> str:
        package = self.directory / name
        package.mkdir()
        path = package / "workflow.yaml"
        path.write_text(textwrap.dedent(source))
        return str(path)


if __name__ == "__main__":
    unittest.main()
