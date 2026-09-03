"""Validates an ordinary sibling batch before model presentation."""

from harness.batch_step_group_validating import BatchStepGroupValidating
from harness.flow_validation_error import FlowValidationError
from harness.step_result import StepResult


"""
solid-name: OrdinaryBatchStepGroupValidator
solid-category: service
solid-spec: [SPEC-042]
solid-description: Enforces unique domain labels and one shared prompt for an ordinary sibling batch.
"""
class OrdinaryBatchStepGroupValidator(BatchStepGroupValidating):
    def validate(self, steps: list[StepResult]) -> None:
        labels = [step.batch.label for step in steps if step.batch is not None]
        if len(labels) != len(set(labels)):
            raise FlowValidationError(
                "Batch for_each labels must resolve to unique strings"
            )
        prompt = steps[0].prompt
        if any(step.prompt != prompt for step in steps[1:]):
            raise FlowValidationError(
                "Every item in a batch for_each step must resolve to the same prompt"
            )
