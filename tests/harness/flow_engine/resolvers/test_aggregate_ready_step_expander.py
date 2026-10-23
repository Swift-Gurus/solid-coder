"""Tests aggregate presentation expansion over original ready work."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.aggregate_ready_step_expander_factory import (
    AggregateReadyStepExpanderFactory,
)
from harness.batch_step_group_identity import BatchStepGroupIdentity
from harness.batch_step_presentation import BatchStepPresentation
from harness.flow_def import FlowDef
from harness.flow_engine_assembly_factory import FlowEngineAssemblyFactory
from harness.for_each_declaration import ForEachDeclaration
from harness.run_state import RunState
from harness.step_def import StepDef
from harness.step_instance import StepInstance
from harness.step_output_reference import StepOutputReference
from harness.workflow_context_value import WorkflowContextValue
from harness.workflow_context_values import WorkflowContextValues
from harness.workflow_execution_mode import WorkflowExecutionMode
from harness.workflow_presentation_mode import WorkflowPresentationMode
from harness.workflow_run_context import WorkflowRunContext

"""
solid-name: TestAggregateReadyStepExpander
solid-category: unit-test
solid-spec: [SPEC-045]
solid-description: Proves aggregate phases become original step instances with typed model-presentation identities.
"""


class TestAggregateReadyStepExpander(unittest.TestCase):
    def setUp(self) -> None:
        self.sut = AggregateReadyStepExpanderFactory().make(
            FlowEngineAssemblyFactory().build().interpolator
        )

    def test_materializes_each_run_with_its_supplied_context(self) -> None:
        flow = FlowDef(
            id="context-flow",
            name="Context Flow",
            max_turns=10,
            execution=WorkflowExecutionMode.AGGREGATE,
            steps=[
                StepDef(id="inspect", prompt="Inspect."),
                StepDef(
                    id="decide",
                    prompt="Decide {{params.label}}.",
                    depends_on=["inspect"],
                ),
            ],
        )
        state = RunState(completed={}, running=[], turn_count=0, status="running")
        ready = [StepInstance("inspect", "inspect-1", None, "Inspect.")]

        for label in ("first", "second"):
            context = WorkflowRunContext(
                parameters=WorkflowContextValues(
                    entries=[WorkflowContextValue("label", label)]
                )
            )

            expansion = self.sut.expand(flow, state, ready, context)

            self.assertEqual(expansion.ready[-1].prompt, f"Decide {label}.")

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

        expanded = self.sut.expand(flow, state, ready, WorkflowRunContext()).ready

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

        expanded = self.sut.expand(flow, state, ready, WorkflowRunContext()).ready

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

        expanded = self.sut.expand(flow, state, ready, WorkflowRunContext()).ready

        self.assertEqual(
            [instance.instance_id for instance in expanded],
            ["review-1", "review-2"],
        )
        self.assertEqual(
            [instance.batch.label for instance in expanded],
            ["A", "B"],
        )

    def test_operation_iteration_cannot_seed_an_independent_model_phase(self) -> None:
        flow = FlowDef(
            id="aggregate-flow",
            name="Aggregate Flow",
            max_turns=10,
            execution=WorkflowExecutionMode.AGGREGATE,
            steps=[
                StepDef(
                    id="count",
                    type="operation",
                    prompt="",
                    for_each=ForEachDeclaration(
                        source=StepOutputReference("prepare", "items")
                    ),
                ),
                StepDef(id="inspect", prompt="Inspect."),
                StepDef(id="decide", prompt="Decide.", depends_on=["inspect"]),
            ],
        )
        state = RunState(completed={}, running=[], turn_count=0, status="running")
        operation = StepInstance(
            step_id="count",
            instance_id="count-3",
            item=["padding", "frame"],
            prompt="",
            iteration_index=2,
        )
        ready = [operation, StepInstance("inspect", "inspect-1", None, "Inspect.")]

        expanded = self.sut.expand(flow, state, ready, WorkflowRunContext()).ready

        self.assertIs(expanded[0], operation)
        self.assertEqual(
            [instance.instance_id for instance in expanded],
            ["count-3", "inspect-1", "decide-1"],
        )
        self.assertEqual(
            [instance.iteration_index for instance in expanded],
            [2, None, None],
        )
        self.assertEqual([instance.item for instance in expanded[1:]], [None, None])

    def test_mixed_ready_loops_and_scalar_keep_their_own_context(self) -> None:
        flow = FlowDef(
            id="mixed",
            name="Mixed",
            max_turns=10,
            execution=WorkflowExecutionMode.AGGREGATE,
            presentation=WorkflowPresentationMode.COMBINED,
            steps=[
                StepDef(
                    id="left",
                    prompt="Left.",
                    for_each=ForEachDeclaration(StepOutputReference("prepare", "left")),
                ),
                StepDef(id="scalar", prompt="Scalar."),
                StepDef(
                    id="right",
                    prompt="Right.",
                    for_each=ForEachDeclaration(
                        StepOutputReference("prepare", "right")
                    ),
                ),
            ],
        )
        state = RunState(completed={}, running=[], turn_count=0, status="running")
        ready = [
            StepInstance("left", "left-1", "A", "Left A.", iteration_index=0),
            StepInstance("left", "left-2", "B", "Left B.", iteration_index=1),
            StepInstance("scalar", "scalar-1", None, "Scalar."),
            StepInstance("right", "right-1", "C", "Right C.", iteration_index=0),
        ]

        expanded = self.sut.expand(flow, state, ready, WorkflowRunContext()).ready

        self.assertEqual(
            [step.instance_id for step in expanded],
            [step.instance_id for step in ready],
        )
        self.assertEqual([step.item for step in expanded], ["A", "B", None, "C"])
        self.assertEqual(
            [step.prompt for step in expanded], [step.prompt for step in ready]
        )
        self.assertTrue(all(step.batch is not None for step in expanded))
        self.assertEqual(len({step.batch.group for step in expanded}), 1)
        self.assertEqual(len({step.batch.label for step in expanded}), 4)

    def test_explicit_individual_iteration_is_not_absorbed_by_ready_scalar_phase(
        self,
    ) -> None:
        flow = FlowDef(
            id="mixed",
            name="Mixed",
            max_turns=10,
            execution=WorkflowExecutionMode.AGGREGATE,
            presentation=WorkflowPresentationMode.COMBINED,
            steps=[
                StepDef(
                    id="individual",
                    prompt="Individual.",
                    for_each=ForEachDeclaration(
                        source=StepOutputReference("prepare", "items"),
                        mode_declared=True,
                    ),
                ),
                StepDef(id="scalar", prompt="Scalar."),
            ],
        )
        state = RunState(completed={}, running=[], turn_count=0, status="running")
        individual = StepInstance(
            "individual", "individual-1", "A", "Individual A.", iteration_index=0
        )
        ready = [individual, StepInstance("scalar", "scalar-1", None, "Scalar.")]

        expansion = self.sut.expand(flow, state, ready, WorkflowRunContext())
        expanded = expansion.ready

        self.assertIs(expanded[0], individual)
        self.assertIsNone(expanded[0].batch)
        self.assertIsNotNone(expanded[1].batch)
        self.assertEqual(
            expansion.phases[0].deferrals[0].reason.value, "execution_policy"
        )
        self.assertIn("Materialized work", expansion.phases[0].deferrals[0].detail)


if __name__ == "__main__":
    unittest.main()
