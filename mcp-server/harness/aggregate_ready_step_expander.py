"""Expands planned aggregate phases over a ready model frontier."""

from harness.aggregate_phase import AggregateExpansion, AggregatePhase
from harness.aggregate_phase_materializing import AggregatePhaseMaterializing
from harness.aggregate_phase_planner import AggregatePhasePlanner
from harness.aggregate_ready_step_expanding import AggregateReadyStepExpanding
from harness.flow_def import FlowDef
from harness.run_state import RunState
from harness.step_instance import StepInstance
from harness.step_instance_boundary_resolving import StepInstanceBoundaryResolving
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: AggregateReadyStepExpander
solid-category: service
solid-spec: [SPEC-045]
solid-description: Replaces eligible ready boundaries with their planned original-step aggregate instances.
"""
class AggregateReadyStepExpander(AggregateReadyStepExpanding):
    def __init__(
        self,
        planner: AggregatePhasePlanner,
        boundary_resolver: StepInstanceBoundaryResolving,
        materializer: AggregatePhaseMaterializing,
    ) -> None:
        self._planner = planner
        self._boundary_resolver = boundary_resolver
        self._materializer = materializer

    def expand(
        self,
        flow: FlowDef,
        state: RunState,
        ready: list[StepInstance],
        context: WorkflowRunContext = WorkflowRunContext(),
    ) -> AggregateExpansion:
        if any(
            instance.skip is not None or instance.automatic_outputs is not None
            for instance in ready
        ):
            return AggregateExpansion(ready=ready)
        phases = self._planner.plan(flow, state, ready)
        if not phases:
            return AggregateExpansion(ready=ready)

        expanded: list[StepInstance] = []
        materialized_phases: list[AggregatePhase] = []
        handled_boundaries: list[str] = []
        for instance in ready:
            boundary_id = self._boundary_resolver.resolve(flow, instance)
            phase = next(
                (
                    candidate
                    for candidate in phases
                    if candidate.boundary_id == boundary_id
                ),
                None,
            )
            if phase is None or instance.step_id not in phase.step_ids:
                expanded.append(instance)
            elif boundary_id not in handled_boundaries:
                phase_ready = [
                    candidate for candidate in ready
                    if candidate.step_id in phase.step_ids
                    and self._boundary_resolver.resolve(flow, candidate) == boundary_id
                ]
                materialized = self._materializer.materialize(flow, phase, phase_ready, context)
                expanded.extend(materialized.ready)
                materialized_phases.extend(materialized.phases)
                handled_boundaries.append(boundary_id)
        return AggregateExpansion(ready=expanded, phases=materialized_phases)
