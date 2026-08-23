"""Tests nested runtime contexts for included workflow steps."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.included_workflow_step_identities import IncludedWorkflowStepIdentities
from harness.included_workflow_step_identity import IncludedWorkflowStepIdentity
from harness.comparison_condition import ComparisonCondition
from harness.condition_operator import ConditionOperator
from harness.step_skip import StepSkip
from harness.step_outputs import StepOutputs
from harness.unavailable_condition_evidence import UnavailableConditionEvidence
from harness.workflow_expression import WorkflowExpression
from harness.workflow_context_value import WorkflowContextValue
from harness.workflow_context_values import WorkflowContextValues
from harness.workflow_run_context import WorkflowRunContext
from harness.workflow_step_context_resolver import WorkflowStepContextResolver


"""
solid-name: TestWorkflowStepContextResolver
solid-category: unit-test
solid-spec: [SPEC-037]
solid-description: Verifies child workflow contexts expose only their own inputs, source item, and local step outputs.
"""
class TestWorkflowStepContextResolver(unittest.TestCase):

    def test_isolates_local_step_outputs_between_child_instances(self) -> None:
        context = WorkflowRunContext(
            completed_steps=WorkflowContextValues(
                entries=[
                    WorkflowContextValue(
                        name="opaque-alpha-completion",
                        value=StepOutputs(values={"finding": "Alpha inspected"}),
                    ),
                    WorkflowContextValue(
                        name="opaque-beta-completion",
                        value=StepOutputs(values={"finding": "Beta inspected"}),
                    ),
                ]
            )
        )

        first = WorkflowStepContextResolver().resolve(
            context,
            self._workflow_instance(
                index=1,
                source_item="Alpha",
                execution_step_id="opaque-alpha-completion",
            ),
            item="Alpha",
        )
        second = WorkflowStepContextResolver().resolve(
            context,
            self._workflow_instance(
                index=2,
                source_item="Beta",
                execution_step_id="opaque-beta-completion",
            ),
            item="Beta",
        )

        self.assertEqual(
            first.completed_steps.find("inspect").value.get("finding"),
            "Alpha inspected",
        )
        self.assertEqual(
            second.completed_steps.find("inspect").value.get("finding"),
            "Beta inspected",
        )
        self.assertFalse(
            first.completed_steps.find("opaque-beta-completion").present
        )
        self.assertFalse(
            second.completed_steps.find("opaque-alpha-completion").present
        )
        self.assertEqual(first.parameters.find("review_unit").value, "Alpha")
        self.assertEqual(second.parameters.find("review_unit").value, "Beta")

    def test_maps_skipped_child_steps_to_their_local_identity(self) -> None:
        condition = ComparisonCondition(
            reference=WorkflowExpression(value="params.enabled"),
            operator=ConditionOperator.EQUALS,
            expected=True,
        )
        skip = StepSkip(
            step_id="opaque-alpha-completion",
            instance_id="opaque-alpha-completion-1",
            condition=condition,
            evidence=UnavailableConditionEvidence(matched=False),
        )
        context = WorkflowRunContext(
            skipped_steps=WorkflowContextValues(
                entries=[
                    WorkflowContextValue(
                        name="opaque-alpha-completion",
                        value=skip,
                    )
                ]
            )
        )

        resolved = WorkflowStepContextResolver().resolve(
            context,
            self._workflow_instance(
                index=1,
                source_item="Alpha",
                execution_step_id="opaque-alpha-completion",
            ),
            item="Alpha",
        )

        self.assertEqual(resolved.skipped_steps.find("inspect").value, skip)
        self.assertFalse(
            resolved.skipped_steps.find("opaque-alpha-completion").present
        )

    def _workflow_instance(
        self,
        index: int,
        source_item: str,
        execution_step_id: str,
    ) -> IncludedWorkflowInstance:
        instance_id = f"review-{index}"
        return IncludedWorkflowInstance(
            alias="review",
            instance_id=instance_id,
            source_index=index - 1,
            source_item=source_item,
            inputs=WorkflowContextValues(
                entries=[
                    WorkflowContextValue(
                        name="review_unit",
                        value=source_item,
                    )
                ]
            ),
            steps=IncludedWorkflowStepIdentities(
                entries=[
                    IncludedWorkflowStepIdentity(
                        declaration_id="review.inspect",
                        local_step_id="inspect",
                        execution_step_id=execution_step_id,
                    )
                ]
            ),
        )


if __name__ == "__main__":
    unittest.main()
