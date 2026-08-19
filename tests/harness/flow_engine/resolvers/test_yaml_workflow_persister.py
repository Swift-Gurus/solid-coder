"""
solid-name: TestYamlWorkflowPersister
solid-description: Validates durable workflow snapshots retain the public conditional grammar.
solid-category: unit-test
"""

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.comparison_condition import ComparisonCondition
from harness.condition_operator import ConditionOperator
from harness.workflow_expression import WorkflowExpression
from harness.flow_def import FlowDef
from harness.flow_engine_assembly_factory import FlowEngineAssemblyFactory
from harness.include_alias_group import IncludeAliasGroup
from harness.step_def import StepDef
from harness.workflow_persister_factory import make_workflow_persister


class TestYamlWorkflowPersister(unittest.TestCase):

    def test_persists_workflow_and_step_conditions_using_public_when_grammar(self):
        workflow_condition = ComparisonCondition(
            reference=WorkflowExpression(value="params.enabled"),
            operator=ConditionOperator.EQUALS,
            expected=True,
        )
        step_condition = ComparisonCondition(
            reference=WorkflowExpression(
                value="steps.inspect.outputs.language"
            ),
            operator=ConditionOperator.EQUALS,
            expected="swift",
        )
        flow = FlowDef(
            id="conditional-review",
            name="Conditional Review",
            max_turns=10,
            condition=workflow_condition,
            steps=[
                StepDef(
                    id="review",
                    prompt="Review the change",
                    condition=step_condition,
                )
            ],
            alias_groups=[
                IncludeAliasGroup(
                    alias="swift_review",
                    member_ids=["review"],
                    condition=step_condition,
                )
            ],
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            run_directory = Path(temporary_directory)
            make_workflow_persister().persist(run_directory, flow)
            workflow_path = run_directory / "workflow.yaml"
            snapshot = yaml.safe_load(workflow_path.read_text())
            reloaded = FlowEngineAssemblyFactory().build().flow_loader.load(
                str(workflow_path),
                [],
            )

        self.assertEqual(
            snapshot["when"],
            {"ref": "{{params.enabled}}", "equals": True},
        )
        self.assertEqual(
            snapshot["steps"][0]["when"],
            {
                "ref": "{{steps.inspect.outputs.language}}",
                "equals": "swift",
            },
        )
        self.assertNotIn("condition", snapshot)
        self.assertNotIn("condition", snapshot["steps"][0])
        self.assertEqual(
            snapshot["alias_groups"][0]["when"],
            {
                "ref": "{{steps.inspect.outputs.language}}",
                "equals": "swift",
            },
        )
        self.assertNotIn("condition", snapshot["alias_groups"][0])
        self.assertEqual(reloaded.condition, workflow_condition)
        self.assertEqual(reloaded.steps[0].condition, step_condition)
        self.assertEqual(reloaded.alias_groups[0].condition, step_condition)


if __name__ == "__main__":
    unittest.main()
