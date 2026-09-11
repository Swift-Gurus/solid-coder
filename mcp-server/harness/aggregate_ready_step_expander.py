"""Expands planned aggregate phases over a ready model frontier."""

from harness.aggregate_phase_materializing import AggregatePhaseMaterializing
from harness.aggregate_phase_planner import AggregatePhasePlanner
from harness.aggregate_ready_step_expanding import AggregateReadyStepExpanding
from harness.flow_def import FlowDef
from harness.run_state import RunState
from harness.step_instance import StepInstance
from harness.step_instance_boundary_resolving import StepInstanceBoundaryResolving


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
    ) -> list[StepInstance]:
        if any(
            instance.skip is not None or instance.automatic_outputs is not None
            for instance in ready
        ):
            return ready
        phases = self._planner.plan(flow, state, ready)
        if not phases:
            return ready

        expanded: list[StepInstance] = []
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
            if phase is None:
                expanded.append(instance)
            elif boundary_id not in handled_boundaries or (
                instance.iteration_index is not None
                and instance.step_id == phase.step_ids[0]
            ):
                expanded.extend(self._materializer.materialize(flow, phase, instance))
                if boundary_id not in handled_boundaries:
                    handled_boundaries.append(boundary_id)
        return expanded
