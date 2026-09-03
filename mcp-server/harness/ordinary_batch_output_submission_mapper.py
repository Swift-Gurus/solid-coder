"""Maps ordinary domain-keyed batch outputs to ready instances."""

from harness.batch_submission_target import BatchSubmissionTarget
from harness.models import StepInstance
from harness.step_output_submission_mapping import StepOutputSubmissionMapping
from harness.step_output_submission_mapping_result import (
    StepOutputSubmissionMappingResult,
)


"""
solid-name: OrdinaryBatchOutputSubmissionMapper
solid-category: service
solid-spec: [SPEC-042]
solid-description: Translates ordinary domain-labelled batch outputs into existing ready workflow instances.
"""
class OrdinaryBatchOutputSubmissionMapper(StepOutputSubmissionMapping):
    def map(
        self,
        ready: list[StepInstance],
        outputs: dict,
    ) -> StepOutputSubmissionMappingResult:
        group = ready[0].batch.group
        targets = [
            BatchSubmissionTarget(
                label=instance.batch.label,
                instance_id=instance.instance_id,
            )
            for instance in ready
            if instance.batch is not None and instance.batch.group == group
        ]
        labels = [target.label for target in targets]
        if len(labels) != len(set(labels)):
            return StepOutputSubmissionMappingResult(
                outputs={},
                error="Batch for_each labels must resolve to unique strings",
            )

        mapped_outputs = {}
        for label, value in outputs.items():
            target = next(
                (candidate for candidate in targets if candidate.label == label),
                None,
            )
            if target is None:
                return StepOutputSubmissionMappingResult(
                    outputs={},
                    error=f"Unknown batch item label '{label}'",
                )
            mapped_outputs[target.instance_id] = value
        return StepOutputSubmissionMappingResult(outputs=mapped_outputs)
