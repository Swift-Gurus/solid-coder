"""Characterizes loading runtime metadata for dynamic workflow includes."""

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.comparison_condition import ComparisonCondition
from harness.condition_operator import ConditionOperator
from harness.flow_engine_assembly_factory import FlowEngineAssemblyFactory
from harness.flow_validation_error import FlowValidationError
from harness.step_output_reference import StepOutputReference
from harness.workflow_expression import WorkflowExpression


class TestDynamicWorkflowIncludeLoading(unittest.TestCase):

    def setUp(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.directory = Path(temporary_directory.name)
        self.loader = FlowEngineAssemblyFactory().build().flow_loader

    def test_preserves_runtime_fields_on_the_include_group(self) -> None:
        self._write_child_workflow()
        parent = self._write_parent_workflow()

        flow = self.loader.load(str(parent), [])

        group = flow.alias_groups[0]
        self.assertEqual(group.alias, "review")
        self.assertEqual(group.member_ids, ["review.inspect"])
        self.assertEqual(group.depends_on, ["prepare"])
        self.assertEqual(
            group.for_each,
            StepOutputReference(step_id="prepare", output_name="units"),
        )
        self.assertEqual(
            [(binding.name, binding.expression) for binding in group.input_bindings],
            [("review_unit", WorkflowExpression(value="item"))],
        )
        self.assertEqual(
            group.condition,
            ComparisonCondition(
                reference=WorkflowExpression(value="item.language"),
                operator=ConditionOperator.EQUALS,
                expected="swift",
            ),
        )

    def test_does_not_copy_group_runtime_fields_onto_child_steps(self) -> None:
        self._write_child_workflow()
        parent = self._write_parent_workflow()

        flow = self.loader.load(str(parent), [])

        child_step = next(step for step in flow.steps if step.id == "review.inspect")
        self.assertEqual(child_step.depends_on, [])
        self.assertIsNone(child_step.for_each)
        self.assertIsNone(child_step.condition)

    def test_rejects_an_unknown_include_dependency(self) -> None:
        self._write_child_workflow()
        parent = self.directory / "unknown-dependency.yaml"
        parent.write_text(
            textwrap.dedent(
                """
                name: parent
                steps:
                  - include: child.yaml
                    as: review
                    depends_on: [missing]
                """
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "depends on unknown step 'missing'",
        ):
            self.loader.load(str(parent), [])

    def test_rejects_a_for_each_source_that_is_not_an_include_dependency(self) -> None:
        self._write_child_workflow()
        parent = self.directory / "non-upstream-source.yaml"
        parent.write_text(
            textwrap.dedent(
                """
                name: parent
                steps:
                  - id: prepare
                    prompt: Prepare units.
                    outputs:
                      - name: units
                        type: data
                        schema:
                          type: array
                  - include: child.yaml
                    as: review
                    for_each: "{{steps.prepare.outputs.units}}"
                """
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "must reference a transitive dependency",
        ):
            self.loader.load(str(parent), [])

    def _write_child_workflow(self) -> None:
        (self.directory / "child.yaml").write_text(
            textwrap.dedent(
                """
                id: child-review
                name: child_review
                steps:
                  - id: inspect
                    prompt: Inspect the mapped review unit.
                """
            ),
            encoding="utf-8",
        )

    def _write_parent_workflow(self) -> Path:
        path = self.directory / "parent.yaml"
        path.write_text(
            textwrap.dedent(
                """
                name: parent
                steps:
                  - id: prepare
                    prompt: Prepare units.
                    outputs:
                      - name: units
                        type: data
                        schema:
                          type: array
                          items:
                            type: object
                            properties:
                              language: {type: string}
                            required: [language]
                  - include: child.yaml
                    as: review
                    depends_on: [prepare]
                    for_each: "{{steps.prepare.outputs.units}}"
                    with:
                      review_unit: "{{item}}"
                    when:
                      ref: "{{item.language}}"
                      equals: swift
                """
            ),
            encoding="utf-8",
        )
        return path


if __name__ == "__main__":
    unittest.main()
