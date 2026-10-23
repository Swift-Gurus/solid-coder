"""Collects compatible model steps within one aggregate boundary."""

from __future__ import annotations

from harness.aggregate_phase import (
    AggregateDeferralReason,
    AggregatePhase,
    AggregatePhaseDeferral,
)
from harness.aggregate_phase_step_collecting import AggregatePhaseStepCollecting
from harness.flow_def import FlowDef
from harness.for_each_mode import ForEachMode
from harness.run_state import RunState
from harness.step_def import StepDef
from harness.step_instance import StepInstance
from harness.workflow_execution_mode import WorkflowExecutionMode
from harness.workflow_step_boundary_resolving import WorkflowStepBoundaryResolving

_MODEL_OWNED_STEP_TYPES = frozenset({"agent", "metric", "exception"})


"""
solid-name: AggregatePhaseStepCollector
solid-category: service
solid-spec: [SPEC-045]
solid-description: Collects dependency-ordered model steps without crossing workflow or execution boundaries.
"""


class AggregatePhaseStepCollector(AggregatePhaseStepCollecting):
    def __init__(self, boundary_resolver: WorkflowStepBoundaryResolving) -> None:
        self._boundary_resolver = boundary_resolver

    def collect(
        self,
        flow: FlowDef,
        state: RunState,
        first: StepDef,
        boundary_id: str,
        ready: list[StepInstance],
    ) -> AggregatePhase:
        selected: list[str] = []
        deferrals: list[AggregatePhaseDeferral] = []
        selected_ids: set[str] = set()
        settled_ids = set(state.completed) | set(state.skipped)
        ready_ids = {instance.step_id for instance in ready}
        execution = (
            first.workflow_instance.execution
            if first.workflow_instance
            else flow.execution
        )

        for candidate in flow.steps:
            if candidate.id in settled_ids or candidate.id in state.running:
                continue
            candidate_boundary = self._boundary_resolver.resolve(flow, candidate)
            pending = [
                dependency
                for dependency in candidate.depends_on
                if dependency not in settled_ids and dependency not in selected_ids
            ]
            if candidate_boundary != boundary_id:
                deferrals.append(
                    AggregatePhaseDeferral(
                        candidate.id,
                        candidate_boundary,
                        AggregateDeferralReason.WORKFLOW_BOUNDARY,
                    )
                )
                continue
            if (
                execution is WorkflowExecutionMode.GRANULAR
                and candidate.id not in ready_ids
            ):
                deferrals.append(
                    AggregatePhaseDeferral(
                        candidate.id,
                        boundary_id,
                        AggregateDeferralReason.EXECUTION_POLICY,
                        pending,
                        "Effective execution mode is granular.",
                    )
                )
                continue
            if candidate.metric_calculation is not None:
                # Metrics stay engine-owned. Their position must not hide
                # independent classifiers; consumers still wait because an
                # uncalculated metric is not in settled_ids or selected_ids.
                deferrals.append(
                    AggregatePhaseDeferral(
                        candidate.id,
                        boundary_id,
                        AggregateDeferralReason.ENGINE_OWNED_STEP,
                        pending,
                        "MCP must calculate this metric before its consumers can proceed.",
                    )
                )
                continue
            if candidate.type not in _MODEL_OWNED_STEP_TYPES:
                deferrals.append(
                    AggregatePhaseDeferral(
                        candidate.id,
                        boundary_id,
                        AggregateDeferralReason.ENGINE_OWNED_STEP,
                        pending,
                        f"Step type: {candidate.type}.",
                    )
                )
                continue
            if candidate.condition is not None and candidate.id not in ready_ids:
                deferrals.append(
                    AggregatePhaseDeferral(
                        candidate.id,
                        boundary_id,
                        AggregateDeferralReason.UNAVAILABLE_CONDITION,
                        pending,
                    )
                )
                continue
            if candidate.for_each is not None and candidate.id not in ready_ids:
                reason = (
                    AggregateDeferralReason.EXECUTION_POLICY
                    if candidate.for_each.mode_declared
                    and candidate.for_each.mode is ForEachMode.INDIVIDUAL
                    else AggregateDeferralReason.UNAVAILABLE_COLLECTION
                )
                deferrals.append(
                    AggregatePhaseDeferral(candidate.id, boundary_id, reason, pending)
                )
                continue
            if candidate.id != first.id and pending:
                deferrals.append(
                    AggregatePhaseDeferral(
                        candidate.id,
                        boundary_id,
                        AggregateDeferralReason.PENDING_VALIDATION,
                        pending,
                    )
                )
                continue

            selected.append(candidate.id)
            if candidate.for_each is None:
                selected_ids.add(candidate.id)

        return AggregatePhase(
            boundary_id=boundary_id, step_ids=selected, deferrals=deferrals
        )
