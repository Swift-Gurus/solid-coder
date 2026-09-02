"""Selects ready model-facing siblings belonging to one batch group."""

from harness.flow_validation_error import FlowValidationError
from harness.sibling_batch_step_selecting import SiblingBatchStepSelecting
from harness.step_result import StepResult


"""
solid-name: SiblingBatchStepSelector
solid-category: service
solid-spec: [SPEC-042]
solid-description: Selects one ready batch group and enforces unique domain labels before it is presented to the model.
"""
class SiblingBatchStepSelector(SiblingBatchStepSelecting):
    def select(
        self,
        selected: StepResult,
        steps: list[StepResult],
    ) -> list[StepResult]:
        if selected.batch is None:
            return [selected]
        siblings = [
            step
            for step in steps
            if step.batch is not None
            and step.batch.group == selected.batch.group
        ]
        labels = [step.batch.label for step in siblings if step.batch is not None]
        if len(labels) != len(set(labels)):
            raise FlowValidationError(
                "Batch for_each labels must resolve to unique strings"
            )
        prompt = siblings[0].prompt
        if any(step.prompt != prompt for step in siblings[1:]):
            raise FlowValidationError(
                "Every item in a batch for_each step must resolve to the same prompt"
            )
        return siblings
