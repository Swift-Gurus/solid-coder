"""Assembles aggregate ready-step expansion."""

from harness.aggregate_phase_materializer import AggregatePhaseMaterializer
from harness.aggregate_phase_planner import AggregatePhasePlanner
from harness.aggregate_phase_step_collector import AggregatePhaseStepCollector
from harness.aggregate_ready_step_expander import AggregateReadyStepExpander
from harness.aggregate_step_eligibility_checker import AggregateStepEligibilityChecker
from harness.step_instance_boundary_resolver import StepInstanceBoundaryResolver
from harness.workflow_step_boundary_resolver import WorkflowStepBoundaryResolver
from harness.workflow_step_finder import WorkflowStepFinder


"""
solid-name: AggregateReadyStepExpanderFactory
solid-category: factory
solid-spec: [SPEC-045]
solid-description: Assembles aggregate phase planning and original-step instance materialization.
"""
class AggregateReadyStepExpanderFactory:
    def make(self) -> AggregateReadyStepExpander:
        step_finder = WorkflowStepFinder()
        boundary_resolver = StepInstanceBoundaryResolver()
        return AggregateReadyStepExpander(
            planner=AggregatePhasePlanner(
                step_finder=step_finder,
                boundary_resolver=boundary_resolver,
                eligibility_checker=AggregateStepEligibilityChecker(),
                step_collector=AggregatePhaseStepCollector(
                    boundary_resolver=WorkflowStepBoundaryResolver(),
                ),
            ),
            boundary_resolver=boundary_resolver,
            materializer=AggregatePhaseMaterializer(step_finder=step_finder),
        )
