"""Selects ready model-facing siblings belonging to one batch group."""

from harness.batch_step_group_validator_resolving import (
    BatchStepGroupValidatorResolving,
)
from harness.sibling_batch_step_selecting import SiblingBatchStepSelecting
from harness.step_result import StepResult


"""
solid-name: SiblingBatchStepSelector
solid-category: service
solid-spec: [SPEC-042]
solid-description: Chooses the ready sibling steps belonging to one supported batch presentation.
"""
class SiblingBatchStepSelector(SiblingBatchStepSelecting):
    def __init__(self, validators: BatchStepGroupValidatorResolving) -> None:
        self._validators = validators

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
        self._validators.resolve(selected.batch.mode).validate(siblings)
        return siblings
