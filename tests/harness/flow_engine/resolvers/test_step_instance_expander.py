"""Tests expansion of executable workflow-step definitions."""

from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.included_workflow_step_identities import IncludedWorkflowStepIdentities
from harness.included_workflow_step_identity import IncludedWorkflowStepIdentity
from harness.models import RunState, StepDef, StepOutputs
from harness.step_instance_builder import StepInstanceBuilder
from harness.step_instance_expander import StepInstanceExpander
from harness.workflow_context_value import WorkflowContextValue
from harness.workflow_context_values import WorkflowContextValues
from harness.workflow_run_context import WorkflowRunContext
from harness.workflow_step_context_resolver import WorkflowStepContextResolver
from harness.workflow_results_visibility_selector import (
    WorkflowResultsVisibilitySelector,
)


@dataclass(frozen=True)
class ReviewUnit:
    name: str


class StubItemsResolver:
    def resolve(self, step_id, expression, context):
        raise AssertionError("A non-iterated child step must not resolve another collection")


class StubRenderer:
    def render(self, template: str, context: WorkflowRunContext) -> str:
        review_unit = context.parameters.find("review_unit").value
        finding = context.completed_steps.find("inspect").value.get("finding")
        return (
            template
            .replace("{{params.review_unit.name}}", review_unit.name)
            .replace("{{steps.inspect.outputs.finding}}", finding)
        )


class UnexpectedOperationInputsResolver:
    def resolve(self, operation, context):
        raise AssertionError("This fixture does not declare an operation step")


class NoBatchPresentationResolver:
    def resolve(self, step, context):
        return None


"""
solid-name: TestStepInstanceExpander
solid-category: unit-test
solid-spec: [SPEC-030, SPEC-037]
solid-description: Verifies that executable step instances preserve iteration and included-workflow source associations.
"""
class TestStepInstanceExpander(unittest.TestCase):

    def test_preserves_included_workflow_source_association(self) -> None:
        source_item = ReviewUnit(name="Beta")
        workflow_instance = IncludedWorkflowInstance(
            alias="review",
            instance_id="review-2",
            source_index=1,
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
                        execution_step_id="review-2.inspect",
                    ),
                    IncludedWorkflowStepIdentity(
                        declaration_id="review.report",
                        local_step_id="report",
                        execution_step_id="review-2.report",
                    ),
                ]
            ),
        )
        step = StepDef(
            id="review-2.report",
            prompt=(
                "Report {{params.review_unit.name}} using "
                "{{steps.inspect.outputs.finding}}."
            ),
            workflow_instance=workflow_instance,
        )
        context_resolver = WorkflowStepContextResolver(
            WorkflowResultsVisibilitySelector()
        )
        sut = StepInstanceExpander(
            items_resolver=StubItemsResolver(),
            context_resolver=context_resolver,
            instance_builder=StepInstanceBuilder(
                renderer=StubRenderer(),
                context_resolver=context_resolver,
                operation_inputs_resolver=UnexpectedOperationInputsResolver(),
                batch_presentation_resolver=NoBatchPresentationResolver(),
            ),
        )

        instances = sut.expand(
            step,
            context=WorkflowRunContext(
                completed_steps=WorkflowContextValues(
                    entries=[
                        WorkflowContextValue(
                            name="review-1.inspect",
                            value=StepOutputs(
                                values={"finding": "Alpha inspected"}
                            ),
                        ),
                        WorkflowContextValue(
                            name="review-2.inspect",
                            value=StepOutputs(
                                values={"finding": "Beta inspected"}
                            ),
                        ),
                    ]
                )
            ),
            run_state=RunState(
                completed={},
                running=[],
                turn_count=0,
                status="in_progress",
            ),
        )

        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0].workflow_instance, workflow_instance)
        self.assertEqual(instances[0].item, source_item)
        self.assertEqual(
            instances[0].prompt,
            "Report Beta using Beta inspected.",
        )
        self.assertIsNone(instances[0].iteration_index)


if __name__ == "__main__":
    unittest.main()
