"""Advances workflow-level condition state before step execution."""

from __future__ import annotations

from harness.condition_decision_evaluating import ConditionDecisionEvaluating
from harness.flow_def import FlowDef
from harness.run_context_building import RunContextBuilding
from harness.run_state import RunState
from harness.workflow_condition_advancing import WorkflowConditionAdvancing
from harness.workflow_condition_decision import WorkflowConditionDecision
from harness.workflow_condition_gate_result import WorkflowConditionGateResult
from harness.workflow_condition_recording import WorkflowConditionRecording


"""
solid-name: WorkflowConditionGate
solid-category: service
solid-spec: [SPEC-037]
solid-description: Coordinates durable workflow eligibility before any workflow step executes.
"""
class WorkflowConditionGate(WorkflowConditionAdvancing):

    def __init__(
        self,
        context_builder: RunContextBuilding,
        condition_evaluator: ConditionDecisionEvaluating,
        decision_recorder: WorkflowConditionRecording,
    ) -> None:
        self._context_builder = context_builder
        self._condition_evaluator = condition_evaluator
        self._decision_recorder = decision_recorder

    def advance(
        self,
        events_path: str,
        flow_def: FlowDef,
        params: dict,
        run_state: RunState,
    ) -> WorkflowConditionGateResult:
        condition = flow_def.condition
        if condition is None:
            return WorkflowConditionGateResult(
                progressed=False,
                allows_execution=True,
            )

        existing_decision = run_state.workflow_condition_decision
        if existing_decision is not None:
            return WorkflowConditionGateResult(
                progressed=False,
                allows_execution=existing_decision.matched,
            )

        context = self._context_builder.build(params, run_state)
        decision = WorkflowConditionDecision(
            condition=condition,
            matched=self._condition_evaluator.evaluate(condition, context),
        )
        self._decision_recorder.record(events_path, decision)
        return WorkflowConditionGateResult(
            progressed=True,
            allows_execution=decision.matched,
        )
