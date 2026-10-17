"""Tests audit identity retained while grouping executable rule steps."""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from harness.flow_def import FlowDef  # noqa: E402
from harness.included_rule_workflow import IncludedRuleWorkflow  # noqa: E402
from harness.included_workflow_instance import IncludedWorkflowInstance  # noqa: E402
from harness.rule_declaration import RuleDeclaration  # noqa: E402
from harness.rule_execution_instances_resolver import (  # noqa: E402
    RuleExecutionInstancesResolver,
)
from harness.run_state import RunState  # noqa: E402
from harness.step_def import StepDef  # noqa: E402
from harness.workflow_context_value import WorkflowContextValue
from harness.workflow_context_values import WorkflowContextValues
from source.source_unit_identity import SourceUnitIdentity


"""
solid-name: TestRuleExecutionInstancesResolver
solid-category: unit-test
solid-spec: [SPEC-039, SPEC-041]
solid-description: Verifies finalized dynamic rule groups retain their include alias and normalized source index for audit attribution.
"""
class TestRuleExecutionInstancesResolver(unittest.TestCase):
    def test_retains_dynamic_rule_source_identity(self) -> None:
        rule = IncludedRuleWorkflow(
            workflow_id="srp",
            declaration=RuleDeclaration(),
        )
        workflow_instance = IncludedWorkflowInstance(
            alias="rule_reviews.srp",
            instance_id="rule_reviews.srp-2",
            source_index=1,
            source_item="second unit",
            rule_workflow=rule,
            inputs=WorkflowContextValues(entries=[WorkflowContextValue(name="review_unit", value="normalized-unit")]),
        )
        flow = FlowDef(
            name="review",
            max_turns=10,
            steps=[
                StepDef(
                    id="rule_reviews.srp-2.measure",
                    prompt="Measure",
                    workflow_instance=workflow_instance,
                )
            ],
        )
        completion = Mock()
        completion.evaluate.return_value = True
        identities = Mock()
        identities.resolve.return_value = SourceUnitIdentity(
            source_identity="/project/Feature.swift", unit_identity="protocol:Reading",
        )

        instances = RuleExecutionInstancesResolver(completion, identities).resolve(
            flow,
            RunState(
                completed={},
                running=[],
                turn_count=0,
                status="running",
            ),
            "root",
        )

        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0].provenance.kind, "included")
        self.assertEqual(
            instances[0].provenance.scope_identity,
            "rule_reviews.srp",
        )
        self.assertEqual(instances[0].provenance.source_index, 1)
        self.assertEqual(instances[0].provenance.source_unit.source_identity, "/project/Feature.swift")
        self.assertEqual(instances[0].provenance.source_unit.unit_identity, "protocol:Reading")
        identities.resolve.assert_called_once_with(workflow_instance.inputs)


if __name__ == "__main__":
    unittest.main()
