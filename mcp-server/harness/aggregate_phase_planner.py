"""Coordinates aggregate model-phase planning."""

from __future__ import annotations

from harness.aggregate_phase import AggregatePhase
from harness.aggregate_phase_step_collecting import AggregatePhaseStepCollecting
from harness.aggregate_step_eligibility_checking import AggregateStepEligibilityChecking
from harness.flow_def import FlowDef
from harness.run_state import RunState
from harness.step_instance import StepInstance
from harness.step_instance_boundary_resolving import StepInstanceBoundaryResolving
from harness.workflow_step_finder import WorkflowStepFinding


"""
solid-name: AggregatePhasePlanner
solid-category: service
solid-spec: [SPEC-045]
solid-description: Coordinates aggregate phase selection through focused workflow-planning capabilities.
"""
class AggregatePhasePlanner:
    def __init__(
        self,
        step_finder: WorkflowStepFinding,
        boundary_resolver: StepInstanceBoundaryResolving,
        eligibility_checker: AggregateStepEligibilityChecking,
        step_collector: AggregatePhaseStepCollecting,
    ) -> None:
        self._step_finder = step_finder
        self._boundary_resolver = boundary_resolver
        self._eligibility_checker = eligibility_checker
        self._step_collector = step_collector

    def plan(
        self,
        flow: FlowDef,
        state: RunState,
        ready: list[StepInstance],
    ) -> list[AggregatePhase]:
        phases: list[AggregatePhase] = []
        planned_boundaries: set[str] = set()

        for instance in ready:
            step = self._step_finder.find(flow, instance.step_id)
            boundary_id = self._boundary_resolver.resolve(flow, instance)
            if boundary_id in planned_boundaries:
                continue
            if not self._eligibility_checker.is_eligible(flow, instance, step):
                continue

            step_ids = self._step_collector.collect(flow, state, step, boundary_id)
            if step_ids:
                phases.append(
                    AggregatePhase(boundary_id=boundary_id, step_ids=step_ids)
                )
                planned_boundaries.add(boundary_id)

        return phases
