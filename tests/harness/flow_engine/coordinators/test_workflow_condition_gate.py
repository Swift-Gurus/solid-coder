"""
solid-name: TestWorkflowConditionGate
solid-description: Validates durable workflow-level condition decisions and replay behavior.
solid-category: unit-test
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.comparison_condition import ComparisonCondition
from harness.condition_operator import ConditionOperator
from harness.flow_def import FlowDef
from harness.run_state import RunState
from harness.workflow_condition_decision import WorkflowConditionDecision
from harness.workflow_condition_gate import WorkflowConditionGate
from harness.workflow_condition_gate_result import WorkflowConditionGateResult
from harness.workflow_context_value import WorkflowContextValue
from harness.workflow_context_values import WorkflowContextValues
from harness.workflow_run_context import WorkflowRunContext


class StubContextBuilder:
    def __init__(self, context: WorkflowRunContext) -> None:
        self.context = context
        self.calls = []

    def build(self, params, run_state):
        self.calls.append((params, run_state))
        return self.context


class StubConditionEvaluator:
    def __init__(self, matched: bool) -> None:
        self.matched = matched
        self.calls = []

    def evaluate(self, condition, context) -> bool:
        self.calls.append((condition, context))
        return self.matched


class SpyWorkflowConditionRecorder:
    def __init__(self) -> None:
        self.calls = []

    def record(self, events_path, decision) -> None:
        self.calls.append((events_path, decision))


def _condition() -> ComparisonCondition:
    return ComparisonCondition(
        reference="{{params.enabled}}",
        operator=ConditionOperator.EQUALS,
        expected=True,
    )


def _flow(condition=None) -> FlowDef:
    return FlowDef(
        name="conditional",
        max_turns=10,
        steps=[],
        condition=condition,
    )


def _state(decision=None) -> RunState:
    return RunState(
        completed={},
        running=[],
        turn_count=0,
        status="in_progress",
        workflow_condition_decision=decision,
    )


class TestWorkflowConditionGate(unittest.TestCase):

    def test_evaluates_and_records_the_first_workflow_decision(self):
        condition = _condition()
        context_builder = StubContextBuilder(
            WorkflowRunContext(
                parameters=WorkflowContextValues(
                    entries=[
                        WorkflowContextValue(name="enabled", value=False)
                    ]
                )
            )
        )
        evaluator = StubConditionEvaluator(matched=False)
        recorder = SpyWorkflowConditionRecorder()
        sut = WorkflowConditionGate(context_builder, evaluator, recorder)

        result = sut.advance(
            "events.jsonl",
            _flow(condition),
            {"enabled": False},
            _state(),
        )

        decision = WorkflowConditionDecision(condition=condition, matched=False)
        self.assertEqual(
            result,
            WorkflowConditionGateResult(progressed=True, allows_execution=False),
        )
        self.assertEqual(evaluator.calls, [(condition, context_builder.context)])
        self.assertEqual(recorder.calls, [("events.jsonl", decision)])

    def test_replayed_false_decision_blocks_without_reevaluation(self):
        decision = WorkflowConditionDecision(condition=_condition(), matched=False)
        context_builder = StubContextBuilder(WorkflowRunContext())
        evaluator = StubConditionEvaluator(matched=True)
        recorder = SpyWorkflowConditionRecorder()
        sut = WorkflowConditionGate(context_builder, evaluator, recorder)

        result = sut.advance(
            "events.jsonl",
            _flow(decision.condition),
            {},
            _state(decision),
        )

        self.assertEqual(
            result,
            WorkflowConditionGateResult(progressed=False, allows_execution=False),
        )
        self.assertEqual(context_builder.calls, [])
        self.assertEqual(evaluator.calls, [])
        self.assertEqual(recorder.calls, [])

    def test_replayed_true_decision_allows_execution_without_reevaluation(self):
        decision = WorkflowConditionDecision(condition=_condition(), matched=True)
        context_builder = StubContextBuilder(WorkflowRunContext())
        evaluator = StubConditionEvaluator(matched=False)
        recorder = SpyWorkflowConditionRecorder()
        sut = WorkflowConditionGate(context_builder, evaluator, recorder)

        result = sut.advance(
            "events.jsonl",
            _flow(decision.condition),
            {},
            _state(decision),
        )

        self.assertEqual(
            result,
            WorkflowConditionGateResult(progressed=False, allows_execution=True),
        )
        self.assertEqual(context_builder.calls, [])
        self.assertEqual(evaluator.calls, [])
        self.assertEqual(recorder.calls, [])

    def test_workflow_without_condition_allows_execution(self):
        context_builder = StubContextBuilder({})
        evaluator = StubConditionEvaluator(matched=False)
        recorder = SpyWorkflowConditionRecorder()
        sut = WorkflowConditionGate(context_builder, evaluator, recorder)

        result = sut.advance("events.jsonl", _flow(), {}, _state())

        self.assertEqual(
            result,
            WorkflowConditionGateResult(progressed=False, allows_execution=True),
        )
        self.assertEqual(context_builder.calls, [])
        self.assertEqual(evaluator.calls, [])
        self.assertEqual(recorder.calls, [])


if __name__ == "__main__":
    unittest.main()
