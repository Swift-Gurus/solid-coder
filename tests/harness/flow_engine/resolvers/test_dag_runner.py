"""
solid-name: TestDAGRunner
solid-description: Validates step readiness determination based on dependencies, completion status, and execution constraints.
solid-category: unit-test
"""

import sys
import unittest
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.dag_runner import DAGRunner
from harness.empty_step_instance_renderer import EmptyStepInstanceRenderer
from harness.expression_resolver import ExpressionResolver
from harness.filter_resolver import FilterResolver
from harness.for_each_items_resolver import ForEachItemsResolver
from harness.interpolator import Interpolator
from harness.models import FlowDef, OutputSpec, RunState, StepDef, StepOutputs
from harness.step_dependency_checker import StepDependencyChecker
from harness.step_instance_completion import StepInstanceCompletion
from harness.step_instance_expander import StepInstanceExpander
from harness.step_instance_renderer import StepInstanceRenderer
from harness.step_readiness_checker import StepReadinessChecker
from harness.step_status_checker import StepStatusChecker


def _make_runner() -> DAGRunner:
    resolver = ExpressionResolver(filter_resolver=FilterResolver())
    return DAGRunner(
        readiness_checker=StepReadinessChecker(
            status_checker=StepStatusChecker(),
            dependency_checker=StepDependencyChecker(),
        ),
        instance_expander=StepInstanceExpander(
            items_resolver=ForEachItemsResolver(evaluator=resolver),
            instance_renderer=StepInstanceRenderer(
                renderer=Interpolator(evaluator=resolver)
            ),
            empty_instance_renderer=EmptyStepInstanceRenderer(),
        ),
    )


class TestDAGRunner(unittest.TestCase):

    def setUp(self):
        self.runner = _make_runner()

    def _flow(self, *steps: StepDef, max_turns: int = 10) -> FlowDef:
        return FlowDef(name="test", max_turns=max_turns, steps=list(steps))

    def _step(self, sid: str, depends_on: Optional[List[str]] = None, for_each: Optional[str] = None) -> StepDef:
        return StepDef(id=sid, prompt=f"Do {sid}", depends_on=depends_on or [], for_each=for_each)

    def _state(self, completed: Optional[List[str]] = None, turn_count: int = 0) -> RunState:
        return RunState(
            completed={s: StepOutputs(values={}) for s in (completed or [])},
            running=[],
            turn_count=turn_count,
            status="in_progress",
        )

    def test_ready_and_blocked_steps(self):
        flow = self._flow(self._step("a"), self._step("b", depends_on=["a"]))
        ids = {i.step_id for i in self.runner.ready_steps(flow, self._state(), {})}
        self.assertIn("a", ids)
        self.assertNotIn("b", ids)
        ids_after = {i.step_id for i in self.runner.ready_steps(flow, self._state(completed=["a"]), {})}
        self.assertIn("b", ids_after)
        self.assertNotIn("a", ids_after)

    def test_completed_step_not_returned(self):
        flow = self._flow(self._step("a"))
        self.assertEqual(self.runner.ready_steps(flow, self._state(completed=["a"]), {}), [])

    def test_for_each_expands_into_n_instances(self):
        step = self._step("review", depends_on=["load"], for_each="{{steps.load.outputs.principles}}")
        flow = self._flow(self._step("load"), step)
        outputs = StepOutputs(values={"principles": ["SRP", "OCP", "LSP"]})
        state = RunState(completed={"load": outputs}, running=[], turn_count=0, status="in_progress")
        instances = self.runner.ready_steps(flow, state, {"steps": {"load": outputs}})
        self.assertEqual(len(instances), 3)
        self.assertEqual({i.item for i in instances}, {"SRP", "OCP", "LSP"})
        self.assertEqual([i.iteration_index for i in instances], [0, 1, 2])

    def test_for_each_returns_only_iterations_not_already_completed(self):
        step = self._step(
            "review",
            depends_on=["load"],
            for_each="{{steps.load.outputs.principles}}",
        )
        flow = self._flow(self._step("load"), step)
        outputs = StepOutputs(values={"principles": ["SRP", "OCP", "LSP"]})
        completed_iteration = StepInstanceCompletion(
            step_id="review",
            instance_id="review-1",
            iteration_index=0,
            item="SRP",
            outputs=StepOutputs(values={"finding": "done"}),
        )
        state = RunState(
            completed={"load": outputs},
            completed_instances={"review-1": completed_iteration},
            running=[],
            turn_count=0,
            status="in_progress",
        )

        instances = self.runner.ready_steps(
            flow,
            state,
            {"steps": {"load": outputs}},
        )

        self.assertEqual(
            [instance.instance_id for instance in instances],
            ["review-2", "review-3"],
        )

    def test_empty_for_each_returns_engine_completion_sentinel(self):
        load = self._step("load")
        review = StepDef(
            id="review",
            prompt="Review {{item}}",
            depends_on=["load"],
            for_each="{{steps.load.outputs.principles}}",
            outputs=[OutputSpec(name="finding", type="data")],
        )
        flow = self._flow(load, review)
        outputs = StepOutputs(values={"principles": []})
        state = RunState(
            completed={"load": outputs},
            running=[],
            turn_count=0,
            status="in_progress",
        )

        instances = self.runner.ready_steps(
            flow,
            state,
            {"steps": {"load": outputs}},
        )

        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0].instance_id, "review-0")
        self.assertEqual(
            instances[0].automatic_outputs,
            StepOutputs(values={"finding": []}),
        )

    def test_returns_empty_when_max_turns_reached(self):
        flow = self._flow(self._step("a"), max_turns=2)
        self.assertEqual(self.runner.ready_steps(flow, self._state(turn_count=2), {}), [])

    def test_parallel_steps_all_returned(self):
        flow = self._flow(self._step("a"), self._step("b"), self._step("c"))
        ids = {i.step_id for i in self.runner.ready_steps(flow, self._state(), {})}
        self.assertEqual(ids, {"a", "b", "c"})


if __name__ == "__main__":
    unittest.main()
