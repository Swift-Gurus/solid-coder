"""Validates a combined rule batch before model presentation."""

from typing import cast

from harness.batch_step_group_validating import BatchStepGroupValidating
from harness.combined_rule_batch_step_presentation import (
    CombinedRuleBatchStepPresentation,
)
from harness.flow_validation_error import FlowValidationError
from harness.step_result import StepResult


"""
solid-name: CombinedRuleBatchStepGroupValidator
solid-category: service
solid-spec: [SPEC-043]
solid-description: Enforces unique rule-and-unit targets and one shared prompt within each rule section of a combined batch.
"""
class CombinedRuleBatchStepGroupValidator(BatchStepGroupValidating):
    def validate(self, steps: list[StepResult]) -> None:
        presentations = [
            cast(CombinedRuleBatchStepPresentation, step.batch)
            for step in steps
        ]
        for index, presentation in enumerate(presentations):
            if any(
                candidate.label == presentation.label
                and candidate.rule_alias == presentation.rule_alias
                for candidate in presentations[index + 1:]
            ):
                raise FlowValidationError(
                    "Combined presentation rule and item labels must be unique"
                )
            if any(
                candidate.rule_alias == presentation.rule_alias
                and steps[candidate_index].prompt != steps[index].prompt
                for candidate_index, candidate in enumerate(presentations)
            ):
                raise FlowValidationError(
                    "Every item for one combined rule must resolve to the same prompt"
                )
