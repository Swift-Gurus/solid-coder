"""Maps nested rule-and-unit batch outputs to ready instances."""

from collections.abc import Mapping
from typing import cast

from harness.batch_submission_target import BatchSubmissionTarget
from harness.combined_rule_batch_step_presentation import (
    CombinedRuleBatchStepPresentation,
)
from harness.models import StepInstance
from harness.step_output_submission_mapping import StepOutputSubmissionMapping
from harness.step_output_submission_mapping_result import (
    StepOutputSubmissionMappingResult,
)


"""
solid-name: CombinedRuleBatchOutputSubmissionMapper
solid-category: service
solid-spec: [SPEC-043]
solid-description: Translates nested domain-and-rule batch outputs into existing ready workflow instances.
"""
class CombinedRuleBatchOutputSubmissionMapper(StepOutputSubmissionMapping):
    def map(
        self,
        ready: list[StepInstance],
        outputs: dict,
    ) -> StepOutputSubmissionMappingResult:
        group = ready[0].batch.group
        targets = [
            BatchSubmissionTarget(
                label=presentation.label,
                workflow_alias=presentation.rule_alias,
                step_id=instance.step_id,
                instance_id=instance.instance_id,
            )
            for instance in ready
            if instance.batch is not None and instance.batch.group == group
            for presentation in [
                cast(CombinedRuleBatchStepPresentation, instance.batch)
            ]
        ]
        for index, target in enumerate(targets):
            if any(
                candidate.label == target.label
                and candidate.workflow_alias == target.workflow_alias
                for candidate in targets[index + 1:]
            ):
                return StepOutputSubmissionMappingResult(
                    outputs={},
                    error=(
                        "Combined presentation rule and item labels must be unique"
                    ),
                )

        mapped_outputs = {}
        for label, rule_outputs in outputs.items():
            if not any(target.label == label for target in targets):
                return StepOutputSubmissionMappingResult(
                    outputs={},
                    error=f"Unknown combined batch item label '{label}'",
                )
            if not isinstance(rule_outputs, Mapping):
                return StepOutputSubmissionMappingResult(
                    outputs={},
                    error=(
                        f"Combined batch item '{label}' must map rule aliases "
                        "to their declared outputs"
                    ),
                )
            for rule_alias, value in rule_outputs.items():
                target = next(
                    (
                        candidate
                        for candidate in targets
                        if candidate.label == label
                        and candidate.workflow_alias == rule_alias
                    ),
                    None,
                )
                if target is None:
                    return StepOutputSubmissionMappingResult(
                        outputs={},
                        error=(
                            f"Unknown combined batch rule alias '{rule_alias}' "
                            f"for item '{label}'"
                        ),
                    )
                mapped_outputs[target.instance_id] = value
        return StepOutputSubmissionMappingResult(outputs=mapped_outputs)
