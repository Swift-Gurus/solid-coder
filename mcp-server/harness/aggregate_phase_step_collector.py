"""Collects compatible model steps within one aggregate boundary."""

from __future__ import annotations

from harness.aggregate_phase_step_collecting import AggregatePhaseStepCollecting
from harness.flow_def import FlowDef
from harness.run_state import RunState
from harness.step_def import StepDef
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
    ) -> list[str]:
        selected: list[str] = []
        selected_ids: set[str] = set()
        settled_ids = set(state.completed) | set(state.skipped)

        for candidate in flow.steps:
            if self._boundary_resolver.resolve(flow, candidate) != boundary_id:
                continue
            if candidate.type not in _MODEL_OWNED_STEP_TYPES:
                if selected:
                    break
                continue
            if candidate.condition is not None:
                break
            if (
                candidate.id in settled_ids
                or candidate.id in state.running
            ):
                continue
            if candidate.id != first.id and (
                first.for_each is not None or candidate.for_each is not None
            ):
                break
            if candidate.id != first.id and not all(
                dependency in settled_ids or dependency in selected_ids
                for dependency in candidate.depends_on
            ):
                continue

            selected.append(candidate.id)
            selected_ids.add(candidate.id)

        return selected
