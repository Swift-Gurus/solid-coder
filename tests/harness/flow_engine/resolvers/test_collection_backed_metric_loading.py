"""Validates loading rules for MCP-owned collection-backed metrics."""

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.all_condition import AllCondition
from harness.flow_engine_assembly_factory import FlowEngineAssemblyFactory
from harness.models import FlowValidationError
from harness.step_output_reference import StepOutputReference


"""
solid-name: TestCollectionBackedMetricLoading
solid-category: unit-test
solid-spec: [SPEC-053]
solid-description: Verifies typed parsing and structural validation for collection-backed metric scoring.
"""
class TestCollectionBackedMetricLoading(unittest.TestCase):
    def setUp(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.directory = Path(temporary_directory.name)
        self.loader = FlowEngineAssemblyFactory().build().flow_loader

    def test_loads_collection_source_and_existing_condition(self) -> None:
        flow = self._load(self._valid_workflow())

        metric = flow.steps[1]
        calculation = metric.metric_calculation
        self.assertEqual(
            calculation.source,
            StepOutputReference(
                step_id="analyze_task_sites",
                output_name="task_sites",
            ),
        )
        self.assertIsInstance(calculation.condition, AllCondition)
        self.assertEqual(metric.prompt, "")
        self.assertEqual(
            [output.name for output in metric.outputs],
            ["value", "additional_info"],
        )

    def test_rejects_non_array_collection_source(self) -> None:
        workflow = self._valid_workflow().replace(
            "type: array",
            "type: object",
            1,
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "source output 'task_sites' must declare an array schema",
        ):
            self._load(workflow)

    def test_rejects_non_integer_collection_metric(self) -> None:
        workflow = self._valid_workflow().replace(
            "type: integer",
            "type: string",
            1,
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "collection-backed metric value must be an integer",
        ):
            self._load(workflow)

    def test_rejects_prompt_on_collection_backed_metric(self) -> None:
        workflow = self._valid_workflow().replace(
            "metric_id: DT-1",
            "metric_id: DT-1\n                    prompt: Count matching task sites.",
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "collection-backed metric must not declare a prompt",
        ):
            self._load(workflow)

    def test_rejects_condition_without_collection_source(self) -> None:
        workflow = self._valid_workflow().replace(
            '                      source: "{{steps.analyze_task_sites.outputs.task_sites}}"\n',
            "",
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "scoring.when requires scoring.source",
        ):
            self._load(workflow)

    def test_rejects_condition_field_absent_from_item_schema(self) -> None:
        workflow = self._valid_workflow().replace(
            "item.classification",
            "item.missing_classification",
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "item field 'missing_classification' is not declared",
        ):
            self._load(workflow)

    def test_rejects_unknown_collection_source_step(self) -> None:
        workflow = self._valid_workflow().replace(
            "steps.analyze_task_sites.outputs.task_sites",
            "steps.missing_analysis.outputs.task_sites",
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "scoring.source references unknown step 'missing_analysis'",
        ):
            self._load(workflow)

    def test_rejects_collection_source_outside_dependency_chain(self) -> None:
        workflow = self._valid_workflow().replace(
            "depends_on: [analyze_task_sites]",
            "depends_on: []",
            1,
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "scoring.source must reference a transitive dependency",
        ):
            self._load(workflow)

    def test_rejects_for_each_on_collection_backed_metric(self) -> None:
        workflow = self._valid_workflow().replace(
            "metric_id: DT-1",
            (
                "metric_id: DT-1\n"
                "                    for_each: "
                '"{{steps.analyze_task_sites.outputs.task_sites}}"'
            ),
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "collection-backed metric must not declare for_each",
        ):
            self._load(workflow)

    def test_rejects_process_execution_on_collection_backed_metric(self) -> None:
        workflow = self._valid_workflow().replace(
            "metric_id: DT-1",
            "metric_id: DT-1\n                    command: echo invalid",
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "collection-backed metric must not declare a process command",
        ):
            self._load(workflow)

    def test_qualifies_collection_source_inside_included_workflow(self) -> None:
        child = self.directory / "child.yaml"
        child.write_text(
            textwrap.dedent(self._valid_workflow()).replace(
                "rule: {}\n",
                "",
                1,
            ),
            encoding="utf-8",
        )
        parent = self.directory / "parent.yaml"
        parent.write_text(
            textwrap.dedent(
                """
                id: parent-review
                name: Parent Review
                max_turns: 5
                rule: {}
                steps:
                  - include: ./child.yaml
                    as: child
                """
            ),
            encoding="utf-8",
        )

        flow = self.loader.load(str(parent), [])

        metric = next(step for step in flow.steps if step.metric is not None)
        self.assertEqual(metric.id, "child.detached_task_count")
        self.assertEqual(
            metric.metric_calculation.source,
            StepOutputReference(
                step_id="child.analyze_task_sites",
                output_name="task_sites",
            ),
        )

    def _load(self, workflow: str):
        path = self.directory / "workflow.yaml"
        path.write_text(textwrap.dedent(workflow), encoding="utf-8")
        return self.loader.load(str(path), [])

    def _valid_workflow(self) -> str:
        return """
                id: detached-task-review
                name: Detached Task Review
                max_turns: 5
                rule: {}
                steps:
                  - id: analyze_task_sites
                    prompt: Classify every task site.
                    outputs:
                      - name: task_sites
                        type: data
                        schema:
                          type: array
                          items:
                            type: object
                            additionalProperties: false
                            required: [classification, is_exception]
                            properties:
                              classification:
                                type: string
                                enum: [DETACHED, UNSTRUCTURED]
                              is_exception: {type: boolean}
                  - id: detached_task_count
                    type: metric
                    metric_id: DT-1
                    depends_on: [analyze_task_sites]
                    value:
                      type: integer
                      minimum: 0
                    scoring:
                      source: "{{steps.analyze_task_sites.outputs.task_sites}}"
                      when:
                        all:
                          - ref: "{{item.classification}}"
                            equals: DETACHED
                          - ref: "{{item.is_exception}}"
                            equals: false
                      severe:
                        operator: greater_than_or_equal
                        value: 1
                  - id: classify_exception
                    type: exception
                    prompt: Decide whether the whole unit is exempt.
                """


if __name__ == "__main__":
    unittest.main()
