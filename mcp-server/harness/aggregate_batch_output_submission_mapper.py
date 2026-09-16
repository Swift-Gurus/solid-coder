"""Maps nested aggregate outputs to original ready instances."""

from collections.abc import Mapping
from typing import cast

from harness.aggregate_envelope_submission_rejecting import (
    AggregateEnvelopeSubmissionRejecting,
)
from harness.aggregate_batch_step_presentation import AggregateBatchStepPresentation
from harness.batch_submission_target import BatchSubmissionTarget
from harness.batch_submission_target_resolving import BatchSubmissionTargetResolving
from harness.models import StepInstance
from harness.step_output_submission_mapping import StepOutputSubmissionMapping
from harness.step_output_submission_mapping_result import StepOutputSubmissionMappingResult
from harness.successful_step_output_mapping_building import SuccessfulStepOutputMappingBuilding


"""
solid-name: AggregateBatchOutputSubmissionMapper
solid-category: service
solid-spec: [SPEC-045, SPEC-052]
solid-description: Translates aggregate item, workflow, and step addresses into original instance outputs.
"""
class AggregateBatchOutputSubmissionMapper(StepOutputSubmissionMapping):
    def __init__(
        self,
        target_resolver: BatchSubmissionTargetResolving,
        success_builder: SuccessfulStepOutputMappingBuilding,
        envelope_rejector: AggregateEnvelopeSubmissionRejecting,
    ) -> None:
        self._target_resolver = target_resolver
        self._success_builder = success_builder
        self._envelope_rejector = envelope_rejector

    def map(
        self,
        ready: list[StepInstance],
        outputs: dict,
    ) -> StepOutputSubmissionMappingResult:
        group = ready[0].batch.group
        targets = [
            BatchSubmissionTarget(
                label=presentation.label,
                workflow_alias=presentation.workflow_alias,
                step_id=presentation.authored_step.step_id,
                instance_id=instance.instance_id,
            )
            for instance in ready
            if instance.batch is not None and instance.batch.group == group
            for presentation in [cast(AggregateBatchStepPresentation, instance.batch)]
        ]

        mapped_outputs = {}
        for item_label, workflows in outputs.items():
            if not any(target.label == item_label for target in targets):
                return self._envelope_rejector.reject(
                    f"Unknown aggregate item label '{item_label}'",
                    targets,
                )
            if not isinstance(workflows, Mapping):
                return self._envelope_rejector.reject(
                    f"Aggregate item '{item_label}' must map workflow aliases to steps",
                    targets,
                )
            for workflow_alias, steps in workflows.items():
                if not isinstance(steps, Mapping):
                    return self._envelope_rejector.reject(
                        f"Aggregate workflow '{workflow_alias}' must map step IDs to outputs",
                        targets,
                    )
                for step_id, value in steps.items():
                    target = self._target_resolver.resolve(
                        targets,
                        item_label,
                        workflow_alias,
                        step_id,
                    )
                    if target is None:
                        return self._envelope_rejector.reject(
                            f"Unknown aggregate address '{item_label} / {workflow_alias} / {step_id}'",
                            targets,
                        )
                    mapped_outputs[target.instance_id] = value
        return self._success_builder.build(mapped_outputs)
