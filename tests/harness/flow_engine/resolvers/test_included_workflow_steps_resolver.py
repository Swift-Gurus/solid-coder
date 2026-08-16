"""Tests materializing one item-scoped included workflow DAG."""

from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.include_alias_group import IncludeAliasGroup
from harness.included_workflow_dependencies_resolver import (
    IncludedWorkflowDependenciesResolver,
)
from harness.included_workflow_identifier_qualifier import (
    IncludedWorkflowIdentifierQualifier,
)
from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.included_workflow_steps_resolver import IncludedWorkflowStepsResolver
from harness.models import StepDef
from harness.resolved_workflow_input import ResolvedWorkflowInput
from harness.workflow_run_context import WorkflowRunContext


@dataclass(frozen=True)
class ReviewUnit:
    name: str


class StubInputResolver:
    def resolve(self, bindings, context: WorkflowRunContext):
        return [
            ResolvedWorkflowInput(
                name="review_unit",
                value=context.item.value,
            )
        ]


class StubRenderer:
    def render(self, template: str, context: WorkflowRunContext) -> str:
        review_unit = context.parameters.find("review_unit").value
        return template.replace(
            "{{params.review_unit.name}}",
            review_unit.name,
        )


"""
solid-name: TestIncludedWorkflowStepsResolver
solid-category: unit-test
solid-spec: [SPEC-037]
solid-description: Verifies that every materialized child step retains its owning workflow instance and source-item association.
"""
class TestIncludedWorkflowStepsResolver(unittest.TestCase):

    def test_associates_each_child_step_with_its_source_item(self) -> None:
        qualifier = IncludedWorkflowIdentifierQualifier()
        sut = IncludedWorkflowStepsResolver(
            input_resolver=StubInputResolver(),
            identifier_qualifier=qualifier,
            dependency_resolver=IncludedWorkflowDependenciesResolver(qualifier),
            renderer=StubRenderer(),
        )
        group = IncludeAliasGroup(
            alias="review",
            member_ids=["review.inspect", "review.report"],
            depends_on=["prepare"],
        )
        source_item = ReviewUnit(name="Beta")

        steps = sut.resolve(
            group=group,
            templates=[
                StepDef(
                    id="review.inspect",
                    prompt="Inspect {{params.review_unit.name}}.",
                ),
                StepDef(
                    id="review.report",
                    prompt="Report {{params.review_unit.name}}.",
                    depends_on=["review.inspect"],
                ),
            ],
            iteration_index=1,
            item=source_item,
            context=WorkflowRunContext(),
        )

        expected_instance = IncludedWorkflowInstance(
            alias="review",
            instance_id="review-2",
            source_index=1,
            source_item=source_item,
        )
        self.assertEqual(
            [step.workflow_instance for step in steps],
            [expected_instance, expected_instance],
        )
        self.assertEqual([step.id for step in steps], ["review-2.inspect", "review-2.report"])
        self.assertEqual(steps[1].depends_on, ["review-2.inspect"])


if __name__ == "__main__":
    unittest.main()
