"""Materializes planned aggregate phases as original step instances."""

from dataclasses import replace

from common.optional_value import OptionalValue
from harness.aggregate_batch_step_group_identity import AggregateBatchStepGroupIdentity
from harness.aggregate_batch_step_presentation import AggregateBatchStepPresentation
from harness.aggregate_phase import (
    AggregateDeferralReason,
    AggregateExpansion,
    AggregatePhase,
    AggregatePhaseDeferral,
)
from harness.aggregate_phase_materializing import AggregatePhaseMaterializing
from harness.authored_step_coordinate import AuthoredStepCoordinate
from harness.flow_def import FlowDef
from harness.interpolation_error import InterpolationError
from harness.interpolator import TemplateRendering
from harness.step_instance import StepInstance
from harness.workflow_run_context import WorkflowRunContext
from harness.workflow_step_context_resolving import WorkflowStepContextResolving
from harness.workflow_step_finder import WorkflowStepFinding

"""
solid-name: AggregatePhaseMaterializer
solid-category: service
solid-spec: [SPEC-045]
solid-description: Materializes planned aggregate work with original step identities and typed presentation metadata.
"""


class AggregatePhaseMaterializer(AggregatePhaseMaterializing):
    def __init__(
        self,
        step_finder: WorkflowStepFinding,
        renderer: TemplateRendering,
        context_resolver: WorkflowStepContextResolving,
    ) -> None:
        self._step_finder = step_finder
        self._renderer = renderer
        self._context_resolver = context_resolver

    def materialize(
        self,
        flow: FlowDef,
        phase: AggregatePhase,
        ready: list[StepInstance],
        context: WorkflowRunContext,
    ) -> AggregateExpansion:
        materialized: list[StepInstance] = []
        deferred: set[str] = set()
        deferrals = list(phase.deferrals)
        for step_id in phase.step_ids:
            step = self._step_finder.find(flow, step_id)
            pending = [
                dependency for dependency in step.depends_on if dependency in deferred
            ]
            if pending:
                deferred.add(step_id)
                deferrals.append(
                    AggregatePhaseDeferral(
                        step_id,
                        phase.boundary_id,
                        AggregateDeferralReason.PENDING_VALIDATION,
                        pending,
                    )
                )
                continue
            seeds = [instance for instance in ready if instance.step_id == step_id]
            if not seeds:
                scope_seed = next(
                    (instance for instance in ready if not instance.is_for_each),
                    ready[0],
                )
                item = (
                    scope_seed.workflow_instance.source_item
                    if scope_seed.workflow_instance
                    else None
                )
                step_context = self._context_resolver.resolve(
                    context, step.workflow_instance, item
                )
                try:
                    prompt = self._renderer.render(step.prompt, step_context)
                    authored_prompt = self._renderer.render(
                        step.authored_prompt or step.prompt, step_context
                    )
                except InterpolationError as error:
                    deferred.add(step_id)
                    deferrals.append(
                        AggregatePhaseDeferral(
                            step_id,
                            phase.boundary_id,
                            AggregateDeferralReason.UNAVAILABLE_RENDER_INPUT,
                            detail=str(error),
                        )
                    )
                    continue
                seeds = [
                    replace(
                        scope_seed,
                        step_id=step_id,
                        instance_id=f"{step_id}-1",
                        item=item,
                        iteration_index=None,
                        prompt=prompt,
                        authored_prompt=authored_prompt,
                        batch=scope_seed.batch if not scope_seed.is_for_each else None,
                    )
                ]
            for seed in seeds:
                materialized.append(
                    self._materialize_step(flow, phase.boundary_id, seed)
                )
        return AggregateExpansion(
            ready=materialized,
            phases=[
                replace(
                    phase,
                    instance_ids=[instance.instance_id for instance in materialized],
                    deferrals=deferrals,
                )
            ],
        )

    def _materialize_step(
        self,
        flow: FlowDef,
        boundary_id: str,
        seed: StepInstance,
    ) -> StepInstance:
        workflow_instance = seed.workflow_instance
        workflow_alias = flow.workflow_id
        presentation_boundary_id = boundary_id
        item_label = (
            OptionalValue.from_nullable(seed.batch)
            .map(lambda batch: batch.label)
            .value_or(seed.instance_id if seed.is_for_each else flow.workflow_id)
        )
        if workflow_instance is not None:
            workflow_alias = workflow_instance.alias
            if workflow_instance.combined_presentation is not None:
                workflow_alias = workflow_instance.combined_presentation.rule_alias
                presentation_boundary_id = (
                    workflow_instance.combined_presentation.group_alias
                )
            item_label = (
                seed.batch.label
                if seed.batch is not None
                else seed.instance_id
                if seed.is_for_each
                else workflow_instance.instance_id
            )

        step = self._step_finder.find(flow, seed.step_id)
        authored_prompt = seed.authored_prompt or seed.prompt
        authored_step_id = step.id
        if workflow_instance is not None:
            authored_step_id = workflow_instance.steps.require_execution(
                step.id
            ).local_step_id
        return replace(
            seed,
            batch=AggregateBatchStepPresentation(
                group=AggregateBatchStepGroupIdentity(
                    presentation_boundary_id=presentation_boundary_id
                ),
                label=item_label,
                workflow_alias=workflow_alias,
                authored_step=AuthoredStepCoordinate(
                    workflow_id=workflow_alias,
                    step_id=authored_step_id,
                    prompt=authored_prompt,
                    outputs=step.outputs,
                ),
            ),
        )
