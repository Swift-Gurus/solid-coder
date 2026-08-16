"""Tests expansion of executable workflow-step definitions."""

from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.models import RunState, StepDef
from harness.step_instance_expander import StepInstanceExpander
from harness.workflow_run_context import WorkflowRunContext


@dataclass(frozen=True)
class ReviewUnit:
    name: str


class StubItemsResolver:
    def resolve(self, step_id, expression, context):
        raise AssertionError("A non-iterated child step must not resolve another collection")


class StubRenderer:
    def render(self, template: str, context: WorkflowRunContext) -> str:
        return template


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
        )
        step = StepDef(
            id="review-2.inspect",
            prompt="Inspect Beta.",
            workflow_instance=workflow_instance,
        )
        sut = StepInstanceExpander(
            items_resolver=StubItemsResolver(),
            renderer=StubRenderer(),
        )

        instances = sut.expand(
            step,
            context=WorkflowRunContext(),
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
        self.assertIsNone(instances[0].iteration_index)


if __name__ == "__main__":
    unittest.main()
