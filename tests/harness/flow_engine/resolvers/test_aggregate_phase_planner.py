"""Tests aggregate model-phase planning across typed workflow boundaries."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.aggregate_phase_planner import AggregatePhasePlanner
from harness.aggregate_phase_step_collector import AggregatePhaseStepCollector
from harness.aggregate_step_eligibility_checker import AggregateStepEligibilityChecker
from harness.flow_def import FlowDef
from harness.for_each_declaration import ForEachDeclaration
from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.run_state import RunState
from harness.step_def import StepDef
from harness.step_instance import StepInstance
from harness.step_instance_boundary_resolver import StepInstanceBoundaryResolver
from harness.step_output_reference import StepOutputReference
from harness.workflow_step_boundary_resolver import WorkflowStepBoundaryResolver
from harness.workflow_step_finder import WorkflowStepFinder
from harness.workflow_execution_mode import WorkflowExecutionMode


"""
solid-name: TestAggregatePhasePlanner
solid-category: unit-test
solid-spec: [SPEC-045]
solid-description: Proves aggregate planning follows the resolved DAG while respecting nested and engine-owned execution boundaries.
"""
class TestAggregatePhasePlanner(unittest.TestCase):
    def setUp(self) -> None:
        self.sut = AggregatePhasePlanner(
            step_finder=WorkflowStepFinder(),
            boundary_resolver=StepInstanceBoundaryResolver(),
            eligibility_checker=AggregateStepEligibilityChecker(),
            step_collector=AggregatePhaseStepCollector(
                boundary_resolver=WorkflowStepBoundaryResolver(),
            ),
        )
        self.state = RunState(
            completed={},
            running=[],
            turn_count=0,
            status="running",
        )

    def test_collects_compatible_dependent_agent_steps_in_topological_order(self) -> None:
        flow = FlowDef(
            id="aggregate",
            name="aggregate",
            max_turns=10,
            steps=[
                StepDef(id="inspect", prompt="Inspect."),
                StepDef(id="measure", prompt="Measure.", depends_on=["inspect"]),
                StepDef(id="decide", prompt="Decide.", depends_on=["measure"]),
            ],
            execution=WorkflowExecutionMode.AGGREGATE,
        )

        phases = self.sut.plan(flow, self.state, [self._ready("inspect")])

        self.assertEqual([phase.step_ids for phase in phases], [["inspect", "measure", "decide"]])

    def test_returns_no_aggregate_phase_for_granular_workflow(self) -> None:
        flow = FlowDef(
            id="granular",
            name="granular",
            max_turns=10,
            steps=[StepDef(id="inspect", prompt="Inspect.")],
        )

        phases = self.sut.plan(flow, self.state, [self._ready("inspect")])

        self.assertEqual(phases, [])

    def test_stops_before_engine_owned_middle_step(self) -> None:
        flow = FlowDef(
            id="aggregate",
            name="aggregate",
            max_turns=10,
            steps=[
                StepDef(id="inspect", prompt="Inspect."),
                StepDef(
                    id="prepare",
                    prompt="",
                    type="operation",
                    depends_on=["inspect"],
                ),
                StepDef(id="report", prompt="Report.", depends_on=["prepare"]),
            ],
            execution=WorkflowExecutionMode.AGGREGATE,
        )

        phases = self.sut.plan(flow, self.state, [self._ready("inspect")])

        self.assertEqual([phase.step_ids for phase in phases], [["inspect"]])

    def test_waits_while_engine_owned_prefix_is_ready(self) -> None:
        flow = FlowDef(
            id="aggregate",
            name="aggregate",
            max_turns=10,
            steps=[
                StepDef(id="prepare", prompt="", type="operation"),
                StepDef(id="report", prompt="Report.", depends_on=["prepare"]),
            ],
            execution=WorkflowExecutionMode.AGGREGATE,
        )

        phases = self.sut.plan(flow, self.state, [self._ready("prepare")])

        self.assertEqual(phases, [])

    def test_waits_while_command_or_script_prefix_is_ready(self) -> None:
        for step_type in ("command", "script"):
            with self.subTest(step_type=step_type):
                flow = FlowDef(
                    id="aggregate",
                    name="aggregate",
                    max_turns=10,
                    steps=[
                        StepDef(id="prepare", prompt="", type=step_type),
                        StepDef(
                            id="report",
                            prompt="Report.",
                            depends_on=["prepare"],
                        ),
                    ],
                    execution=WorkflowExecutionMode.AGGREGATE,
                )

                phases = self.sut.plan(
                    flow,
                    self.state,
                    [self._ready("prepare")],
                )

                self.assertEqual(phases, [])

    def test_stops_before_step_with_unresolved_condition(self) -> None:
        flow = FlowDef(
            id="aggregate",
            name="aggregate",
            max_turns=10,
            steps=[
                StepDef(id="inspect", prompt="Inspect."),
                StepDef(
                    id="conditional",
                    prompt="Conditional.",
                    depends_on=["inspect"],
                    condition=object(),
                ),
            ],
            execution=WorkflowExecutionMode.AGGREGATE,
        )

        phases = self.sut.plan(flow, self.state, [self._ready("inspect")])

        self.assertEqual([phase.step_ids for phase in phases], [["inspect"]])

    def test_stops_before_unmaterialized_for_each_step(self) -> None:
        flow = FlowDef(
            id="aggregate",
            name="aggregate",
            max_turns=10,
            steps=[
                StepDef(id="prepare", prompt="Prepare."),
                StepDef(
                    id="review",
                    prompt="Review.",
                    depends_on=["prepare"],
                    for_each=ForEachDeclaration(
                        source=StepOutputReference("prepare", "items")
                    ),
                ),
            ],
            execution=WorkflowExecutionMode.AGGREGATE,
        )

        phases = self.sut.plan(flow, self.state, [self._ready("prepare")])

        self.assertEqual([phase.step_ids for phase in phases], [["prepare"]])

    def test_stops_after_for_each_step_before_fan_in_dependency(self) -> None:
        flow = FlowDef(
            id="aggregate",
            name="aggregate",
            max_turns=10,
            steps=[
                StepDef(
                    id="review",
                    prompt="Review.",
                    for_each=ForEachDeclaration(
                        source=StepOutputReference("prepare", "items")
                    ),
                ),
                StepDef(
                    id="summarize",
                    prompt="Summarize.",
                    depends_on=["review"],
                ),
            ],
            execution=WorkflowExecutionMode.AGGREGATE,
        )

        phases = self.sut.plan(flow, self.state, [self._ready("review")])

        self.assertEqual([phase.step_ids for phase in phases], [["review"]])

    def test_child_policy_does_not_absorb_parent_sibling(self) -> None:
        child = IncludedWorkflowInstance(
            alias="child",
            instance_id="child-1",
            source_index=0,
            source_item=None,
            execution=WorkflowExecutionMode.AGGREGATE,
        )
        flow = FlowDef(
            id="parent",
            name="parent",
            max_turns=10,
            steps=[
                StepDef(id="child.inspect", prompt="Inspect.", workflow_instance=child),
                StepDef(
                    id="child.measure",
                    prompt="Measure.",
                    depends_on=["child.inspect"],
                    workflow_instance=child,
                ),
                StepDef(id="sibling", prompt="Remain separate."),
            ],
        )

        phases = self.sut.plan(
            flow,
            self.state,
            [
                self._ready("child.inspect", child),
                self._ready("sibling"),
            ],
        )

        self.assertEqual([phase.step_ids for phase in phases], [["child.inspect", "child.measure"]])

    def test_stops_before_delegate_or_session_boundary(self) -> None:
        flow = FlowDef(
            id="aggregate",
            name="aggregate",
            max_turns=10,
            steps=[
                StepDef(id="inspect", prompt="Inspect."),
                StepDef(
                    id="delegate",
                    prompt="Delegate.",
                    type="delegate",
                    mode="session",
                    depends_on=["inspect"],
                ),
                StepDef(id="report", prompt="Report.", depends_on=["delegate"]),
            ],
            execution=WorkflowExecutionMode.AGGREGATE,
        )

        phases = self.sut.plan(flow, self.state, [self._ready("inspect")])

        self.assertEqual([phase.step_ids for phase in phases], [["inspect"]])

    def test_parent_phase_does_not_reopen_completed_child_steps(self) -> None:
        child = IncludedWorkflowInstance(
            alias="child",
            instance_id="child-1",
            source_index=0,
            source_item=None,
            execution=WorkflowExecutionMode.AGGREGATE,
        )
        flow = FlowDef(
            id="parent",
            name="parent",
            max_turns=10,
            steps=[
                StepDef(id="child.inspect", prompt="Inspect.", workflow_instance=child),
                StepDef(
                    id="child.measure",
                    prompt="Measure.",
                    depends_on=["child.inspect"],
                    workflow_instance=child,
                ),
                StepDef(
                    id="parent.report",
                    prompt="Report.",
                    depends_on=["child.measure"],
                ),
            ],
            execution=WorkflowExecutionMode.AGGREGATE,
        )
        resumed = RunState(
            completed={"child.inspect": {}, "child.measure": {}},
            running=[],
            turn_count=1,
            status="running",
        )

        phases = self.sut.plan(
            flow,
            resumed,
            [self._ready("parent.report")],
        )

        self.assertEqual([phase.step_ids for phase in phases], [["parent.report"]])

    @staticmethod
    def _ready(
        step_id: str,
        workflow_instance: IncludedWorkflowInstance | None = None,
    ) -> StepInstance:
        return StepInstance(
            step_id=step_id,
            instance_id=step_id,
            item=None,
            prompt="",
            workflow_instance=workflow_instance,
        )


if __name__ == "__main__":
    unittest.main()
