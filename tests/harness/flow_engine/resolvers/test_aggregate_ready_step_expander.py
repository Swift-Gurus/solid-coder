"""Tests aggregate presentation expansion over original ready work."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.aggregate_ready_step_expander import AggregateReadyStepExpander
from harness.aggregate_phase_materializer import AggregatePhaseMaterializer
from harness.aggregate_phase_planner import AggregatePhasePlanner
from harness.aggregate_phase_step_collector import AggregatePhaseStepCollector
from harness.aggregate_step_eligibility_checker import AggregateStepEligibilityChecker
from harness.batch_step_group_identity import BatchStepGroupIdentity
from harness.batch_step_presentation import BatchStepPresentation
from harness.flow_def import FlowDef
from harness.for_each_declaration import ForEachDeclaration
from harness.run_state import RunState
from harness.step_def import StepDef
from harness.step_instance import StepInstance
from harness.step_instance_boundary_resolver import StepInstanceBoundaryResolver
from harness.step_output_reference import StepOutputReference
from harness.workflow_execution_mode import WorkflowExecutionMode
from harness.workflow_step_boundary_resolver import WorkflowStepBoundaryResolver
from harness.workflow_step_finder import WorkflowStepFinder


"""
solid-name: TestAggregateReadyStepExpander
solid-category: unit-test
solid-spec: [SPEC-045]
solid-description: Proves aggregate phases become original step instances with typed model-presentation identities.
"""
class TestAggregateReadyStepExpander(unittest.TestCase):
    def setUp(self) -> None:
        step_finder = WorkflowStepFinder()
        boundary_resolver = StepInstanceBoundaryResolver()
        self.sut = AggregateReadyStepExpander(
            planner=AggregatePhasePlanner(
                step_finder=step_finder,
                boundary_resolver=boundary_resolver,
                eligibility_checker=AggregateStepEligibilityChecker(),
                step_collector=AggregatePhaseStepCollector(
                    boundary_resolver=WorkflowStepBoundaryResolver(),
                ),
            ),
            boundary_resolver=boundary_resolver,
            materializer=AggregatePhaseMaterializer(step_finder=step_finder),
        )

    def test_expands_dependent_steps_without_replacing_their_identity(self) -> None:
        flow = FlowDef(
            id="aggregate-flow",
            name="Aggregate Flow",
            max_turns=10,
            execution=WorkflowExecutionMode.AGGREGATE,
            steps=[
                StepDef(id="inspect", prompt="Inspect."),
                StepDef(id="decide", prompt="Decide.", depends_on=["inspect"]),
            ],
        )
        state = RunState(completed={}, running=[], turn_count=0, status="running")
        ready = [
            StepInstance(
                step_id="inspect",
                instance_id="inspect-1",
                item=None,
                prompt="Inspect.",
            )
        ]

        expanded = self.sut.expand(flow, state, ready)

        self.assertEqual(
            [instance.step_id for instance in expanded],
            ["inspect", "decide"],
        )
        self.assertEqual(
            [instance.instance_id for instance in expanded],
            ["inspect-1", "decide-1"],
        )
        self.assertEqual(
            [instance.batch.label for instance in expanded],
            ["aggregate-flow", "aggregate-flow"],
        )
        self.assertEqual(
            [instance.batch.workflow_alias for instance in expanded],
            ["aggregate-flow", "aggregate-flow"],
        )

    def test_preserves_granular_ready_instances(self) -> None:
        flow = FlowDef(
            id="granular",
            name="Granular",
            max_turns=10,
            steps=[StepDef(id="inspect", prompt="Inspect.")],
        )
        state = RunState(completed={}, running=[], turn_count=0, status="running")
        ready = [StepInstance("inspect", "inspect-1", None, "Inspect.")]

        expanded = self.sut.expand(flow, state, ready)

        self.assertEqual(expanded, ready)

    def test_preserves_every_ready_instance_of_root_for_each_step(self) -> None:
        flow = FlowDef(
            id="aggregate-flow",
            name="Aggregate Flow",
            max_turns=10,
            execution=WorkflowExecutionMode.AGGREGATE,
            steps=[
                StepDef(
                    id="review",
                    prompt="Review.",
                    for_each=ForEachDeclaration(
                        source=StepOutputReference("prepare", "items")
                    ),
                )
            ],
        )
        state = RunState(completed={}, running=[], turn_count=0, status="running")
        ready = [
            StepInstance(
                step_id="review",
                instance_id=f"review-{index}",
                item=label,
                prompt=f"Review {label}.",
                iteration_index=index - 1,
                batch=BatchStepPresentation(
                    group=BatchStepGroupIdentity(None, "review"),
                    label=label,
                ),
            )
            for index, label in enumerate(["A", "B"], start=1)
        ]

        expanded = self.sut.expand(flow, state, ready)

        self.assertEqual(
            [instance.instance_id for instance in expanded],
            ["review-1", "review-2"],
        )
        self.assertEqual(
            [instance.batch.label for instance in expanded],
            ["A", "B"],
        )


if __name__ == "__main__":
    unittest.main()
