"""Materializes planned aggregate phases as original step instances."""

from common.optional_value import OptionalValue
from harness.aggregate_batch_step_group_identity import AggregateBatchStepGroupIdentity
from harness.aggregate_batch_step_presentation import AggregateBatchStepPresentation
from harness.aggregate_phase import AggregatePhase
from harness.aggregate_phase_materializing import AggregatePhaseMaterializing
from harness.authored_step_coordinate import AuthoredStepCoordinate
from harness.flow_def import FlowDef
from harness.step_instance import StepInstance
from harness.workflow_step_finder import WorkflowStepFinding


"""
solid-name: AggregatePhaseMaterializer
solid-category: service
solid-spec: [SPEC-045]
solid-description: Materializes planned aggregate work with original step identities and typed presentation metadata.
"""
class AggregatePhaseMaterializer(AggregatePhaseMaterializing):
    def __init__(self, step_finder: WorkflowStepFinding) -> None:
        self._step_finder = step_finder

    def materialize(
        self,
        flow: FlowDef,
        phase: AggregatePhase,
        seed: StepInstance,
    ) -> list[StepInstance]:
        workflow_instance = seed.workflow_instance
        workflow_alias = flow.workflow_id
        presentation_boundary_id = phase.boundary_id
        item_label = (
            OptionalValue.from_nullable(seed.batch)
            .map(lambda batch: batch.label)
            .value_or(flow.workflow_id)
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
                else workflow_instance.instance_id
            )

        materialized: list[StepInstance] = []
        for step_id in phase.step_ids:
            step = self._step_finder.find(flow, step_id)
            resolved_prompt = seed.prompt if step.id == seed.step_id else step.prompt
            authored_prompt = (
                seed.authored_prompt or seed.prompt
                if step.id == seed.step_id
                else step.authored_prompt or step.prompt
            )
            authored_step_id = step.id
            if workflow_instance is not None:
                authored_step_id = workflow_instance.steps.require_execution(
                    step.id
                ).local_step_id
            iteration_number = (
                OptionalValue.from_nullable(seed.iteration_index)
                .map(lambda index: index + 1)
                .value_or(1)
            )
            materialized.append(
                StepInstance(
                    step_id=step.id,
                    instance_id=f"{step.id}-{iteration_number}",
                    item=seed.item,
                    prompt=resolved_prompt,
                    authored_prompt=authored_prompt,
                    iteration_index=seed.iteration_index,
                    workflow_instance=workflow_instance,
                    batch=AggregateBatchStepPresentation(
                        group=AggregateBatchStepGroupIdentity(
                            presentation_boundary_id=presentation_boundary_id,
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
            )
        return materialized
